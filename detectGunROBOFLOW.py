from roboflow import Roboflow

# Initialize Roboflow
rf = Roboflow(api_key="QgPuAFG1WvwzQ6fdfP8T")

# Load your project and model version
project = rf.workspace().project("my-first-project-aon9u")
model = project.version("2").model

# Infer on a local image
result = model.predict("ilovevarsha.png", confidence=40, overlap=30).json()

# Print results

if(result['predictions'] != []):
    print("⚠️‼️GUN DETECTED")
    print(result)
else:
    print("🥰NO GUN DETECTED")
    

