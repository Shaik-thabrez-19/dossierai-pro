# final_check.py
import sys
import pkg_resources

def print_header(text):
    print("\n" + "="*60)
    print(f" {text}")
    print("="*60)

def check_package(package_name, import_name=None):
    if import_name is None:
        import_name = package_name.replace('-', '_')
    
    try:
        __import__(import_name)
        version = pkg_resources.get_distribution(package_name).version
        return f"✅ {package_name:<25} v{version:<10} - OK"
    except ImportError:
        try:
            if package_name == 'python-docx':
                __import__('docx')
                version = pkg_resources.get_distribution('python-docx').version
                return f"✅ {package_name:<25} v{version:<10} - OK (as docx)"
            elif package_name == 'docxtpl':
                __import__('docxtpl')
                version = pkg_resources.get_distribution('docxtpl').version
                return f"✅ {package_name:<25} v{version:<10} - OK"
            else:
                return f"❌ {package_name:<25} - NOT FOUND"
        except (ImportError, pkg_resources.DistributionNotFound):
            return f"❌ {package_name:<25} - NOT FOUND"

print_header("📦 DOSSIERAI PACKAGE VERIFICATION")

all_packages = [
    'streamlit', 'pandas', 'numpy', 'plotly',
    'PyPDF2', 'python-docx', 'docxtpl', 'pdfplumber',
    'nltk', 'textblob', 'spacy', 'scikit-learn',
    'reportlab', 'xhtml2pdf', 'fpdf', 'jinja2', 'pdfkit',
    'sqlalchemy', 'psycopg2-binary', 'python-dotenv',
    'matplotlib', 'seaborn',
    'cachetools', 'loguru', 'tqdm', 'requests', 'beautifulsoup4',
    'pytest', 'pytest-cov', 'coverage', 'pygments'
]

print("\n📊 ALL PACKAGES:")
for pkg in all_packages:
    print(check_package(pkg))

print_header("🔍 NLTK DATA CHECK")
try:
    import nltk
    nltk.data.find('tokenizers/punkt')
    print("✅ NLTK punkt - Installed")
except LookupError:
    print("❌ NLTK punkt - Missing")
    print("   Run: python -c \"import nltk; nltk.download('punkt')\"")

try:
    nltk.data.find('corpora/stopwords')
    print("✅ NLTK stopwords - Installed")
except LookupError:
    print("❌ NLTK stopwords - Missing")
    print("   Run: python -c \"import nltk; nltk.download('stopwords')\"")

print_header("🔤 SPACY MODEL CHECK")
try:
    import spacy
    nlp = spacy.load('en_core_web_sm')
    print("✅ spaCy en_core_web_sm - Installed")
except:
    print("❌ spaCy model - Missing")
    print("   Run: python -m spacy download en_core_web_sm")

print_header("🎯 NEXT STEPS")
print("""
1. Download NLTK data:
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger')"

2. Download spaCy model:
   python -m spacy download en_core_web_sm

3. Create .env file:
   echo APP_NAME=DossierAI > .env
   echo APP_VERSION=2.0 >> .env
   echo SECRET_KEY=your-secret-key >> .env

4. Run your app:
   streamlit run app.py
""")