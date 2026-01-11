# Archero2 - Automatic Monster Invasion scores exporter
## Description
If you're tired of tracking the Monster Invasion scores of the guild manually, you can run the script in this project to get all the scores automatically! All you need are screenshots of the Monster invasion leaderboard. 

## Requirements
You can use Python>=3.9 and Python<3.14.

To install Python you can look up tutorials or download it from the [official site](https://www.python.org). **Make sure its one of the compatible versions!** 

It's recommended you also install a package manager. You can use venv or conda. I suggest [conda/miniconda](https://docs.conda.io/projects/conda/en/stable/user-guide/install/index.html). 

After you've installed python and conda, you can create a virtual environment, this way you can isolate the original Python installation.

Replace \<EnvName> with the desired environment name and XX with the desired Python version. 
```cmd
conda create -n <EnvName> python=3.XX
```

Once its created just run
```cmd
conda activate <EnvName>
```

In this environment we can now install the necessary packages and run the code. 
If you open a new terminal you'll have to activate the environment once again on each terminal. 

Install the necessary packages with: 
```shell
pip install -r requirements.txt
```

This project uses easyOCR, if you have [CUDA](https://developer.nvidia.com/cuda-toolkit) installed with GPU support it will process the images faster. If not it will default to CPU and will run slightly slower. To check if CUDA is installed with GPU support in Python, run:
```python
import torch
print(torch.cuda.is_available())
```

## How to use
Create a folder with the images of the MI leaderboard and put the images you want into the desired folder. Structure example:
```text
pathToFolder/
├── MonsterInvasionImages
│   ├── Monday/
│   │    ├── im1.png
│   │    ├── im2.png
│   │    ├── im3.png
│   │         ...
│   ├── Tuesday/
│   ├── Wednesday/
│   ├── Thursday/
│   ├── Friday/
│   ├── Saturday/
│   └── Sunday/
```

### For Windows
Modify the --path argument in the [extractScores.ps1](extractScores.ps1) file with your path to the folder with the images.

**Content example of the file**:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
python monsterInvasion.py --path C:\path\to\folder\MonsterInvasionImages\Monday
```
To execute, open a powershell, activate your environment, navigate to the directory where the file is located and run the ps1 file.
```powershell
conda ativate <EnvName>
cd \pathto\ArcheroOCR
.\extractScores.ps1
```

### For Linux
To be sure it runs correctly execute once so that the file is in unix format. 
```bash
dos2unix extractScores.sh
```

Make the file [extractScores.sh](extractScores.sh) executable.
```bash
chmod +x extractScores.sh
```

Activate the environment and run the file from the same directory as the script:
```bash
conda activate <EnvName>
cd /path/to/ArcheroOCR
./extractScores.sh
``` 

### Output
In both cases you'll see an output of the names in alphabetical order and scores as well as a CSV file with the same in the output folder of the project directory. You can add a --filename argument to the executables to name the resulting CSV file to your liking.

The command line output shows the amount of hits on the boss. It could be that due to reasons an entry in the leaderboard gets skipped. You should still supervise the output and fill the gaps/errors that may occur. 

## Character Recognition (OCR)
This project uses easyOCR. Through testing the reading of the players' scores were very accurate. There were, however, problems with player names especially those with characters not in the latin alphabet. The file [nameCorrection.json](nameCorrection.json) aims to fix this problem.

This file is just a dictionary where you can add incorrect readings of a player's name and it's corrected version. If the output of the OCR coincides with a reading in the file it will correct it to the indicated version. This file is a dictionary so the keys (incorrect names) must not appear more than once in the file. 

The entries on the left are the keys (Incorrect name) and the entries on the right are the values (Correct name)

**Example of file structure and content**
```json
{
    "N4m31": "NAmE1",
    "NAm31": "NAmE1",
    "N4mE1": "NAmE1",
    "Ano1her": "Another",
    "An0ther": "Another"
}
```

Run the program, note the incorrect entries and add it to this file so the next time they are corrected. **If you don't want to do this just leave the file as is DO NOT delete it**. 