import cv2
import mediapipe as mp
import serial
import time

# Inicializa comunicação serial com o Arduino
arduino = serial.Serial('COM3', 9600, timeout=1)
time.sleep(2)

# Inicializa MediaPipe Holistic
mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic
mp_hands = mp.solutions.hands

# Função para verificar se apenas o dedo indicador está levantado
def apenas_dedo_indicador(hand_landmarks):
    dedos_levantados = []

    # Dedo indicador (8) acima do ponto da base (6)
    if hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y:
        dedos_levantados.append(1)
    # Outros dedos
    for tip, pip in [(12, 10), (16, 14), (20, 18)]:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
            dedos_levantados.append(0)
    return dedos_levantados == [1]

# Função para verificar se indicador e médio estão levantados e outros abaixados
def dois_dedos_levantados(hand_landmarks):
    # Verifica cada dedo individualmente
    indicador_up = hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y
    medio_up = hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y
    anelar_down = hand_landmarks.landmark[16].y > hand_landmarks.landmark[14].y
    minimo_down = hand_landmarks.landmark[20].y > hand_landmarks.landmark[18].y
    
    # Precisa indicador e médio levantados, anelar e mínimo abaixados
    return indicador_up and medio_up and anelar_down and minimo_down

# Inicia vídeo
cap = cv2.VideoCapture(0)
ultimo_comando = None
cooldown = 1.0
ultimo_envio = 0

# Sistema de confirmação por frames consecutivos
comando_atual_detectado = None
contador_frames_comando = 0
frames_necessarios = 5  # Precisa detectar o mesmo comando por 5 frames consecutivos
frames_necessarios_normal = 7  # 7 frames para volta ao  estado normal

with mp_holistic.Holistic(model_complexity=1, smooth_landmarks=True) as holistic:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (640, 480))
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = holistic.process(image_rgb)

        mp_drawing.draw_landmarks(frame, results.face_landmarks, mp_holistic.FACEMESH_TESSELATION)
        mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS)
        mp_drawing.draw_landmarks(frame, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
        mp_drawing.draw_landmarks(frame, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS)

        comando = None
        debug_info = "Nenhuma pose detectada"

        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark
            altura_cabeca = lm[mp_holistic.PoseLandmark.NOSE].y - 0.08
            pulso_direito_y = lm[mp_holistic.PoseLandmark.RIGHT_WRIST].y
            altura_linha = int(altura_cabeca * frame.shape[0])
            cv2.line(frame, (0, altura_linha), (frame.shape[1], altura_linha), (255, 0, 255), 2)

            # Debug das condições
            tem_mao_direita = results.right_hand_landmarks is not None
            tem_mao_esquerda = results.left_hand_landmarks is not None
            pulso_acima = pulso_direito_y < altura_cabeca if tem_mao_direita else False

            # Comando 1: Indicador e médio levantados em ambas as mãos
            if tem_mao_esquerda and tem_mao_direita:
                mao_esq_ok = dois_dedos_levantados(results.left_hand_landmarks)
                mao_dir_ok = dois_dedos_levantados(results.right_hand_landmarks)
                
                if mao_esq_ok and mao_dir_ok:
                    comando = '2'
                    debug_info = "Ambas maos com 2 dedos"
                    cv2.putText(frame, "Paciente chamando ajuda", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # = Comando 2: Pulso direito acima da cabeça e só o dedo indicador levantado 
            elif tem_mao_direita and pulso_acima:
                if apenas_dedo_indicador(results.right_hand_landmarks):
                    comando = '1'
                    debug_info = "Pulso direito acima + indicador"
                    cv2.putText(frame, "Paciente sentindo dor", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # = Caso contrário, estado normal, sem chamados de pacientes
            if comando is None:
                comando = '0'
                cv2.putText(frame, "Sem chamados", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        # Mostra informação de debug
        cv2.putText(frame, debug_info, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Sistema de confirmação por frames consecutivos
        if comando == comando_atual_detectado:
            contador_frames_comando += 1
        else:
            comando_atual_detectado = comando
            contador_frames_comando = 1

        # Só processa o comando se foi detectado consistentemente
        comando_confirmado = None
        if contador_frames_comando >= frames_necessarios:
            comando_confirmado = comando_atual_detectado

        # Envia comando apenas se for diferente do anterior e confirmado (evita spamns)
        tempo_atual = time.time()
        if comando_confirmado is not None and comando_confirmado != ultimo_comando:
            arduino.write(comando_confirmado.encode())
            ultimo_comando = comando_confirmado
            ultimo_envio = tempo_atual


        cv2.imshow("Gestos de socorro", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
arduino.close()