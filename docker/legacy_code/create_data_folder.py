import time
import os 

def create_data_folder(): 
    # Get the current time and format
    current_time = time.localtime()
    date_str = time.strftime("%Y_%m_%d", current_time)
    
    # Check if the folder exists
    if not os.path.exists(date_str):
        # If it does not exist, create it
        os.makedirs(date_str)
        if not os.path.exists(date_str):
            print(f"The folder '{date_str}' could not been created.")
        else:
            print(f"The folder '{date_str}' has been created.")
            
    
    # Base path where the folders will be created
    data_path = os.path.join(os.getcwd(), date_str)
    
    # Get all folder names in the base path
    folders = next(os.walk(data_path))[1]
    
    # Filter folders that have at least 3 characters and their first 3 characters are digits, then sort them
    numeric_folders = sorted([f for f in folders if len(f) >= 3 and f[:3].isdigit()], key=lambda x: int(x[:3]))
    
    # Determine the name of the new folder
    if numeric_folders:
        # Find the latest (highest number) folder based on the first 3 digits and add 1
        latest_number = int(numeric_folders[-1][:3])  # Extracting the first 3 digits as the number
        new_data_fp = f"{latest_number + 1:03}"
    else:
    
        # If no numeric folders exist, start with "000"
        new_data_fp = "000"
    
    # Full path for the new folder
    new_data_folder = os.path.join(data_path, new_data_fp)
    
    # Check if the folder exists
    if not os.path.exists(new_data_folder):
        # If it does not exist, create it
        os.makedirs(new_data_folder)
        if not os.path.exists(new_data_folder):
            print(f"The folder '{new_data_folder}' could not been created.")
            # insert exit call
        else:
            print(f"The folder '{new_data_folder}' has been created.")
