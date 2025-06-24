# Use the official Python image from Docker Hub
FROM python:3.11-slim

# Install any dependencies specified in requirements.txt
RUN pip install streamlit

# Expose the port that Streamlit will run on
EXPOSE 8501

# Command to run when the container starts
CMD ["streamlit", "run", "app.py"]