from pydantic import BaseModel, Field
from typing import List
from enum import Enum

# **Categorize Email Output**
class EmailCategory(str, Enum):
    grad_recommendation = "grad_recommendation"
    masters_application = "masters_application"
    phd_application = "phd_application"
    undergrad_internship = "undergrad_internship"
    conference_invitation = "conference_invitation"
    assignment_submission = "assignment_submission"
    other = "other"

class CategorizeEmailOutput(BaseModel):
    category: EmailCategory = Field(
        ..., 
        description="The category assigned to the email, indicating its type based on predefined rules."
    )

# **RAG Query Output**
class RAGQueriesOutput(BaseModel):
    queries: List[str] = Field(
        ..., 
        description="A list of up to three questions representing the customer's intent, based on their email."
    )

# **Email Writer Output**
class WriterOutput(BaseModel):
    email: str = Field(
        ..., 
        description="The draft email written in response to the customer's inquiry, adhering to company tone and standards."
    )

# **Proofreader Email Output**
class ProofReaderOutput(BaseModel):
    feedback: str = Field(
        ..., 
        description="Detailed feedback explaining why the email is or is not sendable."
    )
    send: bool = Field(
        ..., 
        description="Indicates whether the email is ready to be sent (true) or requires rewriting (false)."
    )
