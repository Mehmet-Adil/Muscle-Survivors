import cv2
from mediapipe import solutions as mp_solutions
import pygame


class MovementAnalyser:
    def __init__(self):
        # To make typing easier
        self.mp_draw = mp_solutions.drawing_utils
        self.mp_draw_styles = mp_solutions.drawing_styles
        self.mp_pose = mp_solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.7, min_tracking_confidence=0.7)

        self.cap = cv2.VideoCapture(0)

        self.up_shoulder_positions = self.up_elbow_positions = None
        self.down_shoulder_positions = self.down_elbow_positions = None
        self.mean_up_shoulder_y = 0
        self.mean_down_shoulder_y = 0

        self.body_parts = []

    def get_up_positions(self):
        self.up_shoulder_positions = self.body_parts[11:13]
        self.up_elbow_positions = self.body_parts[13:15]

    def get_down_positions(self):
        self.down_shoulder_positions = self.body_parts[11:13]
        self.down_elbow_positions = self.body_parts[13:15]

    def calculate_setup_means(self):
        self.mean_up_shoulder_y = self.get_mean(self.up_shoulder_positions[0][-1], self.up_shoulder_positions[1][-1])
        self.mean_down_shoulder_y = self.get_mean(self.down_shoulder_positions[0][-1], self.down_shoulder_positions[1][-1])

    @staticmethod
    def get_mean(*arr):
        return sum(arr) / len(arr)

    def get_positions(self):
        if not self.cap.isOpened():
            print("CAMERA IS OFF!")
            return

        success, image = self.cap.read()

        if not success:
            print("EMPTY CAMERA!")
            return

        image = cv2.resize(image, (500, round(500/image.shape[1] * image.shape[0])))
        image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
        result = self.pose.process(image)

        self.body_parts.clear()

        if result.pose_landmarks:
            # Draws the landmarks' points and connects them
            self.mp_draw.draw_landmarks(image, result.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)

            for id, im in enumerate(result.pose_landmarks.landmark):
                h, w, _ = image.shape  # Finding the length and width of the video input
                X, Y = int(im.x * w), int(im.y * h)  # Finding the exact coordinates of the body points

                self.body_parts.append([id, X, Y])

        return image

    @staticmethod
    def show_camera_image(img):
        cv2.waitKey(1)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        cv2.imshow("MUSCLE SURVIVORS",  img)

    @staticmethod
    def convert_cv2_img_to_pygame_img(image):
        """CONVERTS CV2 Image to Pygame Image"""

        return pygame.image.frombuffer(image.tostring(), image.shape[1::-1], "RGB")

    @staticmethod
    def close_camera_window():
        cv2.destroyWindow("MUSCLE SURVIVORS")

    def get_movement_percentage(self):
        if not self.body_parts:  # If AI can't find the shoulders
            return 0

        mean_shoulder_y_now = self.get_mean(self.body_parts[11][-1], self.body_parts[12][-1])

        percentage = -2 * (mean_shoulder_y_now - self.mean_up_shoulder_y) / (
                           self.mean_down_shoulder_y - self.mean_up_shoulder_y) + 1
        percentage = percentage if percentage < 1 else 1
        percentage = percentage if percentage > -1 else -1

        return percentage

    def reset(self):
        self.up_shoulder_positions = self.up_elbow_positions = None
        self.down_shoulder_positions = self.down_elbow_positions = None

        self.mean_up_shoulder_y = 0
        self.mean_down_shoulder_y = 0

        self.body_parts = []

    def close_analyser(self):
        self.cap.release()
        self.pose.close()

