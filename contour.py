import cv2
import base64
import numpy as np
from project.configuration.worker import read_from_json


def draw_contour(frame, min_area=300, max_area=1250):
    flag = read_from_json("project/configuration/position.json", "condition")

    frame_bytes = base64.b64decode(frame)
    np_array = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

    if frame is None or frame.size == 0:
        return None, [], 0.0, 0, [], []

    height, width = frame.shape[:2]
    center_x = width // 2

    top_10_percent = int(height * 0.1)
    bottom_10_percent = int(height * 0.9)

    if flag == 0:
        frame_cropped = frame[0:top_10_percent, 0:width]
    elif flag == 1:
        frame_cropped = frame[bottom_10_percent:height, 0:width]
    else:
        frame_cropped = frame

    hsv = cv2.cvtColor(frame_cropped, cv2.COLOR_BGR2HSV)
    hsv[:, :, 2] = cv2.convertScaleAbs(hsv[:, :, 2], alpha=3.33, beta=0)
    frame_bright = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    gray = cv2.cvtColor(frame_bright, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    frame_with_contours = frame.copy()
    reference_points = []
    y_values = []
    distances = []
    rectangle_widths = []
    dark_percentages = []
    offset_mm = 0.0
    rectangles_count = 0

    mm_to_pixels = 10
    offset_mm_val = 2
    offset_pixels = offset_mm_val * mm_to_pixels

    for contour in contours:
        area = cv2.contourArea(contour)
        if min_area <= area <= max_area:
            rectangles_count += 1
            x, y, w, h = cv2.boundingRect(contour)
            rectangle_widths.append(w)

            if flag == 0:
                rect_y = y
                ref_y = y + offset_pixels
            elif flag == 1:
                rect_y = bottom_10_percent + y
                ref_y = bottom_10_percent + y + h - offset_pixels
            else:
                continue

            if 0 <= ref_y < frame.shape[0]:
                ref_x = x + w // 2
                reference_points.append((ref_x, ref_y))
                y_values.append(ref_y)

                if flag == 0:
                    rect_region = frame[rect_y:rect_y + h, x:x + w]
                else:
                    rect_region = frame[rect_y:rect_y + h, x:x + w]

                gray_region = cv2.cvtColor(rect_region, cv2.COLOR_BGR2GRAY)
                dark_pixels = np.sum(gray_region < 10)
                total_pixels = gray_region.size
                dark_percentage = (dark_pixels / total_pixels) * 100
                dark_percentages.append(dark_percentage)

                if dark_percentage > 10:
                    color = (0, 0, 255)
                else:
                    color = (0, 255, 0)

                cv2.rectangle(frame_with_contours, (x, rect_y), (x + w, rect_y + h), color, 2)

                percentage_text = f"{dark_percentage:.1f}%"
                width_text = f"{w}px"

                text_size1 = cv2.getTextSize(percentage_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                text_size2 = cv2.getTextSize(width_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                text_x1 = x + (w - text_size1[0]) // 2
                text_x2 = x + (w - text_size2[0]) // 2

                if flag == 0:
                    text_y1 = rect_y + h + 15
                    text_y2 = rect_y + h + 35
                else:
                    text_y1 = rect_y - 15
                    text_y2 = rect_y - 35

                cv2.putText(frame_with_contours, percentage_text,
                            (text_x1, text_y1),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3)
                cv2.putText(frame_with_contours, percentage_text,
                            (text_x1, text_y1),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

                cv2.putText(frame_with_contours, width_text,
                            (text_x2, text_y2),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3)
                cv2.putText(frame_with_contours, width_text,
                            (text_x2, text_y2),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

    if len(reference_points) >= 2:
        if y_values:
            fixed_y = int(sum(y_values) / len(y_values))
            reference_points = [(x, fixed_y) for x, y in reference_points]
        reference_points.sort(key=lambda x: x[0])

        if len(reference_points) >= 2:
            left_rect = reference_points[0]
            right_rect = reference_points[-1]

            left_distance = abs(left_rect[0] - center_x)
            right_distance = abs(right_rect[0] - center_x)

            offset_px = left_distance - right_distance
            offset_mm = round(offset_px / mm_to_pixels, 2)

        for i in range(len(reference_points) - 1):
            x1, y1 = reference_points[i]
            x2, y2 = reference_points[i + 1]

            distance = x2 - x1
            distances.append(int(distance))

            mid_x = int((x1 + x2) / 2)
            mid_y = y1

            cv2.line(frame_with_contours, (x1, y1), (x2, y1), (255, 0, 0), 1)
            cv2.putText(frame_with_contours, f"{round(float(distance) / 62.2, 3)}",
                        (mid_x - 20, mid_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        for point in reference_points:
            cv2.circle(frame_with_contours, point, 3, (0, 0, 255), -1)

    _, buffer = cv2.imencode(".jpg", frame_with_contours)
    encoded_image = base64.b64encode(buffer.tobytes()).decode('utf-8')

    return encoded_image, distances, offset_mm, rectangles_count, rectangle_widths, dark_percentages
