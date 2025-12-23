import json
import time
import threading
from datetime import datetime
from flet import *
from project.application.addition.colors import color_mode
from project.application.addition.snake_buttons import change_snake_button_color
from project.configuration.worker import write_to_json, read_from_json
from project.station.requests import move_to_home, move_to_coordinates

robot_lock = threading.Lock()
camera_lock = threading.Lock()


def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {message}")


def main_algorithm(app_page, snake_buttons):
    log_message("🚀 Запуск основного алгоритма")

    def wait_for_processing():
        log_message("⏳ Начало ожидания обработки изображения")
        write_to_json("project/station/statuses.json", "moved_to_cell", 1)
        time.sleep(2.0)
        write_to_json("project/station/statuses.json", "right_view_waiting", 1)

        processing_timeout = 0
        while read_from_json("project/station/statuses.json", "right_view_waiting") == 1:
            time.sleep(0.1)
            processing_timeout += 0.1
            if processing_timeout > 5.0:
                log_message("⚠️ Таймаут обработки изображения")
                break

        write_to_json("project/station/statuses.json", "moved_to_cell", 0)
        log_message("✅ Обработка изображения завершена")

    with open("project/configuration/statistics.json", "w", encoding="utf-8") as file:
        json.dump([], file, ensure_ascii=False, indent=4)

    application_colors = color_mode()
    for button in snake_buttons:
        change_snake_button_color(button, application_colors["inactive"])

    write_to_json("project/configuration/position.json", "condition", 0)

    with robot_lock:
        move_to_home()

    initial_x = read_from_json("project/configuration/coordinates.json", "x_coordinate_of_the_first_cell")
    initial_y = read_from_json("project/configuration/coordinates.json", "y_coordinate_of_the_first_cell")
    initial_z = read_from_json("project/configuration/coordinates.json", "z_coordinate_of_the_first_cell")

    with robot_lock:
        move_to_coordinates(initial_x, initial_y, initial_z)
    time.sleep(10)

    write_to_json("project/station/statuses.json", "moved_to_home", 1)
    time.sleep(2.0)
    write_to_json("project/station/statuses.json", "right_view_waiting", 1)

    initial_processing_timeout = 0
    while read_from_json("project/station/statuses.json", "right_view_waiting") == 1:
        time.sleep(0.1)
        initial_processing_timeout += 0.1
        if initial_processing_timeout > 5.0:
            log_message("⚠️ Таймаут обработки начального изображения")
            break

    write_to_json("project/station/statuses.json", "moved_to_home", 0)

    button_number = 0

    for i in range(3):
        for j in range(10):
            for k in range(2):
                if read_from_json("project/station/statuses.json", "stopped") == 0:
                    while read_from_json("project/station/statuses.json", "paused") != 0:
                        time.sleep(0.1)

                    if k == 0:
                        write_to_json("project/configuration/position.json", "condition", 0)
                        wait_for_processing()

                        distance_state = read_from_json("project/configuration/distances.json", "distances_state")

                        if distance_state == 0:
                            change_snake_button_color(snake_buttons[button_number], colors.GREY)
                        elif distance_state == 1:
                            if snake_buttons[button_number].bgcolor not in (colors.YELLOW, colors.RED):
                                change_snake_button_color(snake_buttons[button_number], colors.GREEN)
                        elif distance_state == 2:
                            if snake_buttons[button_number].bgcolor != colors.RED:
                                change_snake_button_color(snake_buttons[button_number], colors.YELLOW)
                        elif distance_state == 3:
                            change_snake_button_color(snake_buttons[button_number], colors.RED)

                        if distance_state not in (0, 3):
                            with robot_lock:
                                move_to_coordinates(
                                    read_from_json("project/configuration/coordinates.json",
                                                   "current_coordinate_of_the_station_by_x"),
                                    read_from_json("project/configuration/coordinates.json",
                                                   "current_coordinate_of_the_station_by_y") + read_from_json(
                                        "project/configuration/launch.json", "distance_between_vertical_centers") / 2,
                                    read_from_json("project/configuration/coordinates.json",
                                                   "current_coordinate_of_the_station_by_z"))
                        elif distance_state in (0, 3):
                            if j < 9:
                                if i in (0, 2):
                                    with robot_lock:
                                        move_to_coordinates(
                                            read_from_json("project/configuration/coordinates.json",
                                                           "current_coordinate_of_the_station_by_x") + read_from_json(
                                                "project/configuration/launch.json",
                                                "distance_between_horizontal_centers"),
                                            read_from_json("project/configuration/coordinates.json",
                                                           "current_coordinate_of_the_station_by_y"),
                                            read_from_json("project/configuration/coordinates.json",
                                                           "current_coordinate_of_the_station_by_z"))
                                    write_to_json("project/station/statuses.json", "skip_cell", 1)
                                elif i == 1:
                                    with robot_lock:
                                        move_to_coordinates(
                                            read_from_json("project/configuration/coordinates.json",
                                                           "current_coordinate_of_the_station_by_x") - read_from_json(
                                                "project/configuration/launch.json",
                                                "distance_between_horizontal_centers"),
                                            read_from_json("project/configuration/coordinates.json",
                                                           "current_coordinate_of_the_station_by_y"),
                                            read_from_json("project/configuration/coordinates.json",
                                                           "current_coordinate_of_the_station_by_z"))
                                    write_to_json("project/station/statuses.json", "skip_cell", 1)
                            elif j == 9:
                                if i < 2:
                                    with robot_lock:
                                        move_to_coordinates(
                                            read_from_json("project/configuration/coordinates.json",
                                                           "current_coordinate_of_the_station_by_x"),
                                            read_from_json("project/configuration/coordinates.json",
                                                           "current_coordinate_of_the_station_by_y") + read_from_json(
                                                "project/configuration/launch.json",
                                                "distance_between_vertical_centers"),
                                            read_from_json("project/configuration/coordinates.json",
                                                           "current_coordinate_of_the_station_by_z"))
                                    write_to_json("project/station/statuses.json", "skip_cell", 1)
                                else:
                                    write_to_json("project/station/statuses.json", "skip_cell", 1)

                    elif k == 1:
                        if read_from_json("project/station/statuses.json", "skip_cell") == 1:
                            write_to_json("project/station/statuses.json", "skip_cell", 0)
                            button_number += 1
                            continue

                        write_to_json("project/configuration/position.json", "condition", 1)
                        wait_for_processing()

                        distance_state = read_from_json("project/configuration/distances.json", "distances_state")

                        if distance_state == 0:
                            change_snake_button_color(snake_buttons[button_number], colors.GREY)
                        elif distance_state == 1:
                            if snake_buttons[button_number].bgcolor not in (colors.YELLOW, colors.RED):
                                change_snake_button_color(snake_buttons[button_number], colors.GREEN)
                        elif distance_state == 2:
                            if snake_buttons[button_number].bgcolor != colors.RED:
                                change_snake_button_color(snake_buttons[button_number], colors.YELLOW)
                        elif distance_state == 3:
                            change_snake_button_color(snake_buttons[button_number], colors.RED)

                        rectangles_count = 0
                        valid_widths = False
                        valid_dark = False
                        max_attempts = 10
                        attempt = 0

                        while (rectangles_count != 8 or not valid_widths or not valid_dark) and attempt < max_attempts:
                            write_to_json("project/station/statuses.json", "right_view_waiting", 1)
                            time.sleep(0.5)
                            frame_data = read_from_json("project/configuration/distances.json", "last_frame_data")
                            rectangles_count = frame_data.get("rectangles_count", 0) if frame_data else 0
                            rectangle_widths = frame_data.get("rectangle_widths", []) if frame_data else []
                            dark_percentages = frame_data.get("dark_percentages", []) if frame_data else []

                            valid_widths = all(
                                18 <= width <= 28 for width in rectangle_widths) if rectangle_widths else False
                            valid_dark = all(dark_percentage <= 10 for dark_percentage in
                                             dark_percentages) if dark_percentages else False

                            attempt += 1

                        write_to_json("project/station/statuses.json", "right_view_waiting", 0)

                        if j < 9:
                            if i in (0, 2):
                                with robot_lock:
                                    move_to_coordinates(
                                        read_from_json("project/configuration/coordinates.json",
                                                       "current_coordinate_of_the_station_by_x") + read_from_json(
                                            "project/configuration/launch.json", "distance_between_horizontal_centers"),
                                        read_from_json("project/configuration/coordinates.json",
                                                       "current_coordinate_of_the_station_by_y") - read_from_json(
                                            "project/configuration/launch.json",
                                            "distance_between_vertical_centers") / 2,
                                        read_from_json("project/configuration/coordinates.json",
                                                       "current_coordinate_of_the_station_by_z"))
                            elif i == 1:
                                with robot_lock:
                                    move_to_coordinates(
                                        read_from_json("project/configuration/coordinates.json",
                                                       "current_coordinate_of_the_station_by_x") - read_from_json(
                                            "project/configuration/launch.json", "distance_between_horizontal_centers"),
                                        read_from_json("project/configuration/coordinates.json",
                                                       "current_coordinate_of_the_station_by_y") - read_from_json(
                                            "project/configuration/launch.json",
                                            "distance_between_vertical_centers") / 2,
                                        read_from_json("project/configuration/coordinates.json",
                                                       "current_coordinate_of_the_station_by_z"))
                        elif j == 9:
                            if i < 2:
                                with robot_lock:
                                    move_to_coordinates(
                                        read_from_json("project/configuration/coordinates.json",
                                                       "current_coordinate_of_the_station_by_x"),
                                        read_from_json("project/configuration/coordinates.json",
                                                       "current_coordinate_of_the_station_by_y") + read_from_json(
                                            "project/configuration/launch.json",
                                            "distance_between_vertical_centers") / 2,
                                        read_from_json("project/configuration/coordinates.json",
                                                       "current_coordinate_of_the_station_by_z"))
                            else:
                                pass

                        button_number += 1

    write_to_json("project/station/statuses.json", "right_view_waiting", 0)
    write_to_json("project/station/statuses.json", "moved_to_home", 0)
    write_to_json("project/station/statuses.json", "moved_to_cell", 0)
    write_to_json("project/station/statuses.json", "stopped", 0)
    app_page.update()
    return None