import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseConnector:
    """
    Singleton pattern implementation for database connection
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnector, cls).__new__(cls)
            cls._instance._connection = None
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize database connection"""
        try:
            self._connection = psycopg2.connect(
                os.getenv('DATABASE_URL'),
                cursor_factory=RealDictCursor
            )
            print("Database connection established successfully")
        except (Exception, psycopg2.Error) as error:
            print(f"Error connecting to PostgreSQL database: {error}")
            
    def get_connection(self):
        """Get the database connection"""
        if self._connection is None or self._connection.closed:
            self._initialize()
        return self._connection
    
    def execute_query(self, query, params=None):
        """Execute a query and return the results"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute(query, params)
            
            # Check if the query is a SELECT
            if query.lower().strip().startswith('select'):
                results = cursor.fetchall()
                cursor.close()
                return results
            else:
                connection.commit()
                cursor.close()
                return True
        except (Exception, psycopg2.Error) as error:
            print(f"Error executing query: {error}")
            return None
    
    def fetch_student_history(self, student_id):
        """Fetch the student's speaking test history"""
        query = """
        SELECT s.student_id, s.name, s.email, 
               sb.submission_id, sb.submitted_at, 
               sb.fc as fluency_coherence, 
               sb.lr as lexical_resource, 
               sb.gr as grammatical_range, 
               sb.pr as pronunciation,
               sb.overall, sb.overall_comment
        FROM students s
        JOIN submissions sb ON s.student_id = sb.student_id
        WHERE s.student_id = %s
        ORDER BY sb.submitted_at DESC
        """
        return self.execute_query(query, (student_id,))
    
    def save_feedback(self, student_id, fc, lr, gr, pr, overall, overall_comment):
        """
        Save the feedback to the database
        
        Args:
            student_id: Student ID
            fc: Fluency and Coherence score
            lr: Lexical Resource score
            gr: Grammatical Range score
            pr: Pronunciation score
            overall: Overall score
            overall_comment: Overall feedback including teacher comments if available
            
        Returns:
            Submission ID if successful, None otherwise
        """
        query = """
        INSERT INTO submissions 
        (student_id, fc, lr, gr, pr, overall, overall_comment)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING submission_id
        """
        params = (student_id, fc, lr, gr, pr, overall, overall_comment)
        result = self.execute_query(query, params)
        return result[0]['submission_id'] if result else None

# Example usage:
# db = DatabaseConnector()
# student_history = db.fetch_student_history(1) 