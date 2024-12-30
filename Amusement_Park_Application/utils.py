def custom_round_calculate(number):
    remainder = number % 10000
    if remainder <= 5000:
        rounded_number = number - remainder
    else:
        rounded_number = number + (10000 - remainder)
    return rounded_number