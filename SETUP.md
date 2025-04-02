# LingLooma Setup Guide

## Prerequisites

- Python 3.8 or higher
- PostgreSQL database (we're using Neon for this project)
- OpenAI API key

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/linglooma.git
   cd linglooma
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   
   Create a `.env` file in the root directory with the following content:
   ```
   OPENAI_API_KEY=your_openai_api_key
   DATABASE_URL=postgresql://Linglooma_owner:npg_KZsn7Wl3LOdu@ep-snowy-fire-a831dkmt-pooler.eastus2.azure.neon.tech/Linglooma?sslmode=require
   ```
   
   Replace `your_openai_api_key` with your actual OpenAI API key.

4. Initialize the database:
   ```
   python src/database/initialize_db.py
   ```

## Running the Application

Start the Streamlit application:
```
streamlit run src/app/main.py
```

The application will be available at http://localhost:8501.

## Usage

1. Upload a JSON file containing a speaking transcript
2. Enter the student ID 
3. Click on "Start Assessment"
4. When the assessment is complete, review the AI-generated feedback
5. Provide teacher feedback in the text area
6. Submit the feedback to generate the final assessment

## Sample Data

A sample response JSON file is available in the `resources` directory:
```
resources/response.json
```

## Database Structure

The database has two main tables:

1. `students` - Stores student information
   - `student_id` (Primary Key)
   - `name`
   - `email`

2. `submissions` - Stores assessment submissions
   - `submission_id` (Primary Key)
   - `student_id` (Foreign Key)
   - `submitted_at`
   - `fc` (Fluency and Coherence score)
   - `lr` (Lexical Resource score)
   - `gr` (Grammatical Range score)
   - `pr` (Pronunciation score)
   - `overall` (Overall score)
   - `overall_comment`
   - `teacher_feedback` 