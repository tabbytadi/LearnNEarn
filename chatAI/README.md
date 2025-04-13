# Learn&Earn - AI Study Coach

Learn&Earn is an AI-powered study coach that helps you create personalized learning plans and test your knowledge. It uses Google's Gemini AI to generate study materials and assessments based on your input.

## Features

- Generate personalized study plans from PDFs or custom instructions
- Take interactive tests to assess your understanding
- Modern, user-friendly interface
- Real-time progress tracking
- Detailed test results and feedback

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd learn-and-earn
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your Gemini API key:
```
GEMINI_API_KEY=your_api_key_here
```

5. Run the application:
```bash
python app.py
```

6. Open your browser and navigate to the URL shown in the terminal (typically http://127.0.0.1:5000)

## Usage

1. **Generate Study Plan**:
   - Upload a PDF file (optional)
   - Enter custom instructions about what you want to learn
   - Click "Generate Study Plan"

2. **Take Test**:
   - After generating a study plan, click "Take Test"
   - Answer the multiple-choice questions
   - View your results and retake if needed

## Project Structure

```
learn-and-earn/
├── app.py              # Main application file
├── requirements.txt    # Project dependencies
├── .env               # Environment variables
├── templates/         # HTML templates
│   └── index.html     # Main template
└── README.md          # Project documentation
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 