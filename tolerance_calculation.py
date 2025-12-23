from project.configuration.worker import write_to_json, append_distances_to_json


def process_distances(distances, target_value=75):
    """
    Обрабатывает массив расстояний и возвращает результат в зависимости от условий:
    - Если все числа точно равны target_value - возвращает "exact_match" и записывает 1 в JSON
    - Если все числа в пределах target_value ± tolerance -
      возвращает "within_tolerance" и записывает 2 в JSON
    - Если отклонение больше чем ±tolerance - записывает 3 в JSON
    - Если массив пустой - возвращает "out_of_range" и записывает 0 в JSON

    :param distances: список чисел (расстояний)
    :param target_value: целевое значение (по умолчанию 75)
    :return: строка с результатом ("exact_match", "within_tolerance", "out_of_range")
    """
    dst = []
    for distance in distances:
        dst.append(round(float(distance) / 62.2, 3))

    append_distances_to_json(
        "project/configuration/statistics.json",
        dst)

    # Если массив пустой, возвращаем "out_of_range" и записываем 0
    if not distances:
        write_to_json(
            "project/configuration/distances.json",
            "distances_state",
            0)
        return "out_of_range"

    # Проверяем, находятся ли все числа в пределах допуска
    all_within_tolerance = all(
        target_value - 2 <= d <= target_value + 7.46
        for d in distances
    )

    if all_within_tolerance:
        write_to_json(
            "project/configuration/distances.json",
            "distances_state",
            1)
        return "within_tolerance"

    # Если мы попали сюда, значит есть отклонение больше чем ±tolerance
    write_to_json(
        "project/configuration/distances.json",
        "distances_state",
        3)
    return "out_of_range"
