## WESYP ID Card Generator

This project generates personalized ID cards with QR codes for participants, using data from a CSV file and a PDF template.

### Setup

1. **Create and activate a virtual environment (recommended):**
	```sh
	python3 -m venv venv
	source venv/bin/activate
	```

2. **Upgrade pip and install dependencies:**
	```sh
	pip install --upgrade pip
	pip install -r requirements.txt
	```

### Usage

1. Place your participant data in `participants.csv` (format: `participant_id,email,name,country`).
2. Place your ID card template PDF as `id_cards/idcard_template.pdf`.
3. Run the script:
	```sh
	python main.py
	```
4. Generated ID cards will be saved in the `output/` directory, named as `<participant_id>_<name>.pdf`.

### Notes
- The script will automatically create the `output/` directory if it does not exist.
- Each generated PDF will have the participant's name and a QR code with their info.
- Requires Python 3.7+.
