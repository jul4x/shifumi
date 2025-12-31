import cv2
import mediapipe as mp
import random
import time

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def detect_gesture(hand_landmarks):
    """Detecte si la main fait pierre, feuille ou ciseaux"""
    
    # Position des bouts des doigts et articulations
    tips = [8, 12, 16, 20]  # index, majeur, annulaire, auriculaire
    
    fingers_up = []
    
    # Pour chaque doigt (sauf pouce)
    for tip in tips:
        # Si le bout du doigt est au-dessus de l'articulation = doigt leve
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            fingers_up.append(True)
        else:
            fingers_up.append(False)
    
    # Pouce (logique horizontale)
    thumb_up = hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x
    
    # Compter les doigts leves
    count = sum(fingers_up)
    
    # Pierre = poing ferme (0-1 doigts)
    if count <= 1 and not thumb_up:
        return "pierre"
    
    # Ciseaux = index et majeur leves
    elif fingers_up[0] and fingers_up[1] and not fingers_up[2] and not fingers_up[3]:
        return "ciseaux"
    
    # Feuille = main ouverte (4+ doigts)
    elif count >= 3:
        return "feuille"
    
    return None

def get_winner(player, computer):
    """Determine le gagnant"""
    if player == computer:
        return "Egalite!"
    elif (player == "pierre" and computer == "ciseaux") or \
         (player == "ciseaux" and computer == "feuille") or \
         (player == "feuille" and computer == "pierre"):
        return "Tu gagnes!"
    else:
        return "L'ordi gagne!"

def draw_text(frame, text, pos, color=(255, 255, 255), size=1, thickness=2):
    """Affiche du texte avec fond noir pour lisibilite"""
    cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, size, (0, 0, 0), thickness + 2)
    cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, size, color, thickness)

def play_game():
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Scores
    player_score = 0
    computer_score = 0
    
    # Etats du jeu
    game_state = "attente"  # attente, compte, resultat
    countdown_start = 0
    result_start = 0
    player_choice = None
    computer_choice = None
    result_text = ""
    
    with mp_hands.Hands(
        model_complexity=0,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    ) as hands:
        
        while cam.isOpened():
            success, frame = cam.read()
            if not success:
                continue
            
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)
            
            current_gesture = None
            
            # Detecter la main et le geste
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=hand_landmarks,
                        connections=mp_hands.HAND_CONNECTIONS,
                        landmark_drawing_spec=mp_drawing_styles.get_default_hand_landmarks_style(),
                        connection_drawing_spec=mp_drawing_styles.get_default_hand_connections_style(),
                    )
                    current_gesture = detect_gesture(hand_landmarks)
            
            # Machine a etats du jeu
            current_time = time.time()
            
            if game_state == "attente":
                draw_text(frame, "Pierre Feuille Ciseaux!", (120, 50), (0, 255, 255), 1.2)
                draw_text(frame, "Appuie sur ESPACE pour jouer", (140, 100), (255, 255, 255), 0.7)
                draw_text(frame, f"Toi: {player_score}  Ordi: {computer_score}", (220, 450), (255, 255, 0), 0.8)
                
                if current_gesture:
                    draw_text(frame, f"Geste: {current_gesture}", (20, 450), (0, 255, 0), 0.7)
            
            elif game_state == "compte":
                elapsed = current_time - countdown_start
                
                if elapsed < 1:
                    draw_text(frame, "3", (300, 250), (0, 0, 255), 3, 4)
                elif elapsed < 2:
                    draw_text(frame, "2", (300, 250), (0, 165, 255), 3, 4)
                elif elapsed < 3:
                    draw_text(frame, "1", (300, 250), (0, 255, 255), 3, 4)
                elif elapsed < 3.5:
                    draw_text(frame, "MONTRE!", (180, 250), (0, 255, 0), 2, 3)
                else:
                    # Capturer le geste du joueur
                    player_choice = current_gesture
                    computer_choice = random.choice(["pierre", "feuille", "ciseaux"])
                    
                    if player_choice:
                        result_text = get_winner(player_choice, computer_choice)
                        if "Tu gagnes" in result_text:
                            player_score += 1
                        elif "ordi" in result_text:
                            computer_score += 1
                    else:
                        result_text = "Geste non reconnu!"
                    
                    game_state = "resultat"
                    result_start = current_time
            
            elif game_state == "resultat":
                draw_text(frame, f"Toi: {player_choice or '?'}", (50, 200), (255, 200, 0), 1)
                draw_text(frame, f"Ordi: {computer_choice}", (400, 200), (255, 0, 200), 1)
                
                # Couleur selon resultat
                if "Tu gagnes" in result_text:
                    color = (0, 255, 0)
                elif "ordi" in result_text:
                    color = (0, 0, 255)
                else:
                    color = (255, 255, 0)
                
                draw_text(frame, result_text, (200, 300), color, 1.2, 3)
                draw_text(frame, f"Score - Toi: {player_score}  Ordi: {computer_score}", (150, 380), (255, 255, 255), 0.8)
                draw_text(frame, "ESPACE = rejouer  Q = quitter", (150, 450), (200, 200, 200), 0.6)
            
            cv2.imshow("Pierre Feuille Ciseaux", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord(" "):  # Espace
                if game_state in ["attente", "resultat"]:
                    game_state = "compte"
                    countdown_start = time.time()
                    player_choice = None
                    computer_choice = None
    
    cam.release()
    cv2.destroyAllWindows()
    
    print(f"\nScore final - Toi: {player_score}  Ordi: {computer_score}")

if __name__ == "__main__":
    play_game()