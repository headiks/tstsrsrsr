from flet import *
from flet import colors
import time

from project.application.addition.colors import color_mode
from project.application.addition.snake_buttons import change_snake_button_color
from project.station.requests import move_to_coordinates
from project.configuration.worker import read_from_json, write_to_json
from project.station.connection import establish_connection, close_connection


def paint_cell(certain_number, snake_buttons, upper_flag):
    # Цветовая окраска проверяемой ячейки в зависимости от её годности
    distance_state = read_from_json(
        "project/configuration/distances.json",
        "distances_state")

    if distance_state == 0:
        change_snake_button_color(snake_buttons[certain_number - 1], colors.GREY)
    elif distance_state == 1:
        if upper_flag:
            if (snake_buttons[certain_number - 1].bgcolor
                    not in (colors.YELLOW, colors.RED)):
                change_snake_button_color(
                    snake_buttons[certain_number - 1],
                    colors.GREEN)
                write_to_json(
                    "project/configuration/position.json",
                    "condition",
                    1)
        else:
            change_snake_button_color(
                snake_buttons[certain_number - 1],
                colors.GREEN)
            write_to_json(
                "project/configuration/position.json",
                "condition",
                1)
    elif distance_state == 2:
        if upper_flag:
            if snake_buttons[certain_number - 1].bgcolor != colors.RED:
                change_snake_button_color(
                    snake_buttons[certain_number - 1],
                    colors.YELLOW)
                write_to_json(
                    "project/configuration/position.json",
                    "condition",
                    1)
        else:
            change_snake_button_color(
                snake_buttons[certain_number - 1],
                colors.YELLOW)
            write_to_json(
                "project/configuration/position.json",
                "condition",
                1)
    elif distance_state == 3:
        change_snake_button_color(
            snake_buttons[certain_number - 1],
            colors.RED)
        write_to_json("project/configuration/position.json", "condition", 0)

def movement_processing(certain_number, app_page, snake_buttons):
    """
    Перемещение робота на конкретную ячейку палеты и её проверка.

    :param app_page: Страница приложения для обновления цвета
                     ячейки в зависимости от результата проверки
    :param certain_number: Номер ячейки, на которую осуществляется перемещение
    :return: None
    """
    application_colors = color_mode()
    certain_number = int(certain_number) + 1

    connection = establish_connection(app_page)

    if connection is not None:
        x = read_from_json(
            "project/configuration/coordinates.json",
            "x_coordinate_of_the_first_cell")
        y = read_from_json(
            "project/configuration/coordinates.json",
            "y_coordinate_of_the_first_cell")
        z = read_from_json(
            "project/configuration/coordinates.json",
            "z_coordinate_of_the_first_cell")

        dx = 0
        dy = 0

        if 1 <= certain_number <= 10:
            dx = certain_number * read_from_json(
                "project/configuration/launch.json",
                "distance_between_horizontal_centers") - \
                 read_from_json(
                     "project/configuration/launch.json",
                     "distance_between_horizontal_centers")
            x += dx
        elif 11 <= certain_number <= 20:
            dy = read_from_json(
                "project/configuration/launch.json",
                "distance_between_vertical_centers")
            y += dy
            dx = (11 - (certain_number - 10)) * read_from_json(
                "project/configuration/launch.json",
                "distance_between_horizontal_centers") - \
                 read_from_json(
                    "project/configuration/launch.json",
                    "distance_between_horizontal_centers")
            x += dx
        elif 21 <= certain_number <= 30:
            dy = 2 * read_from_json(
                "project/configuration/launch.json",
                "distance_between_vertical_centers")
            y += dy
            dx = (certain_number - 20) * read_from_json(
                "project/configuration/launch.json",
                "distance_between_horizontal_centers") - \
                 read_from_json(
                     "project/configuration/launch.json",
                     "distance_between_horizontal_centers")
            x += dx

        app_page.snack_bar = SnackBar(
            content=Text(
                f"Робот выдвинулся на ячейку {certain_number}. "
                f"Если сделан некорректный снимок, пожалуйста, нажмите на ячейку вновь после остановки робота.",
                font_family="Montserrat",
                size=20,
                weight=FontWeight.W_600,
                color=application_colors["text"]
            ),
            bgcolor=application_colors["red"],
            duration=4000
        )
        app_page.snack_bar.open = True

        move_to_coordinates(connection, x, y, z)
        paint_cell(certain_number, snake_buttons, False)
        write_to_json("project/configuration/position.json", "condition", 0)
        write_to_json(
            "project/station/statuses.json",
            "moved_to_cell",
            1)
        time.sleep(0.5)
        write_to_json(
            "project/station/statuses.json",
            "right_view_waiting",
            1)
        time.sleep(0.5)
        write_to_json(
            "project/station/statuses.json",
            "right_view_waiting",
            0)
        time.sleep(0.5)

        move_to_coordinates(connection, x, y + read_from_json(
            "project/configuration/launch.json",
            "distance_between_vertical_centers"
            ) / 2, z)
        paint_cell(certain_number, snake_buttons, True)
        write_to_json("project/configuration/position.json", "condition", 1)
        time.sleep(0.5)
        write_to_json(
            "project/station/statuses.json",
            "right_view_waiting",
            1)
        time.sleep(0.5)
        write_to_json(
            "project/station/statuses.json",
            "moved_to_cell",
            0)
        write_to_json(
            "project/station/statuses.json",
            "right_view_waiting",
            0)

        close_connection(connection)
    elif connection is None:
        return 0

    return 0
