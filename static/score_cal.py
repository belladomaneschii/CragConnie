IDEAL_TEMP = 14.0      # in Celsius (example)
IDEAL_HUMIDITY = 55.0  # in % (example)
MARGIN = 0.02 # 2%

    

TEMP_WEIGHT = 0.4
HUMIDITY_WEIGHT = 0.4
RATING_WEIGHT = 0.2



    

def calculate_score(current_temp, current_humidity, user_rating):
    """
    Calculate the score based on the current temperature and humidity.
    The score is calculated as follows:
    - If the temperature is within 2% of the ideal temperature, it contributes positively to the score.
    - If the humidity is within 2% of the ideal humidity, it contributes positively to the score.
    - The final score is a percentage of how close the current conditions are to the ideal conditions.
    """
    
    # Calculate differences
    temp_diff = abs(current_temp - IDEAL_TEMP)
    humidity_diff = abs(current_humidity - IDEAL_HUMIDITY)

    temp_score = 1.0 if temp_diff <= IDEAL_TEMP * MARGIN else max(0, 1 - (temp_diff / IDEAL_TEMP))
    humidity_score = 1.0 if humidity_diff <= IDEAL_HUMIDITY * MARGIN else max(0, 1 - (humidity_diff / IDEAL_HUMIDITY))
    
    rating_score = user_rating / 5.0


    # Calculate final score
    final_score = (
    TEMP_WEIGHT * temp_score +
    HUMIDITY_WEIGHT * humidity_score +
    RATING_WEIGHT * rating_score
    )
    
    return final_score * 100 


print(calculate_score(14.0, 55.0, 5))  # Example usage

print
    
    