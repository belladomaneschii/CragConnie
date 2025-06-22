IDEAL_TEMP = 14.0
IDEAL_HUMIDITY = 55.0  
MARGIN = 0.02 

TEMP_WEIGHT = 0.4
HUMIDITY_WEIGHT = 0.4
RATING_WEIGHT = 0.2

def calculate_score(current_temp, current_humidity, user_rating):

    
    temp_diff = abs(current_temp - IDEAL_TEMP)
    humidity_diff = abs(current_humidity - IDEAL_HUMIDITY)

    temp_score = 1.0 if temp_diff <= IDEAL_TEMP * MARGIN else max(0, 1 - (temp_diff / IDEAL_TEMP))
    humidity_score = 1.0 if humidity_diff <= IDEAL_HUMIDITY * MARGIN else max(0, 1 - (humidity_diff / IDEAL_HUMIDITY))
    
    rating_score = user_rating / 5.0

    final_score = (
    TEMP_WEIGHT * temp_score +
    HUMIDITY_WEIGHT * humidity_score +
    RATING_WEIGHT * rating_score
    )
    
    return final_score * 100 

    
    