import os
from dotenv import load_dotenv

load_dotenv()

# Vulnerability: Leaking mock service keys and deep coupling to Supabase Cloud
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://mock-project.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mock-anon-key")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "mock-service-role-key-admin-override")
