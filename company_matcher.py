import pandas as pd
from difflib import SequenceMatcher
import re

# 1. FILE PATH: Make sure this name matches exactly what is in your folder!
# If your file is named "presales_data_sample - presales_data_sample.csv", keep it exactly like this.
file_name = "presales_data_sample - presales_data_sample.csv" 
df = pd.read_csv(file_name)

def clean_name(name):
    if pd.isna(name):
        return ""
    name = str(name).lower()
    name = re.sub(r'[^\w\s]', '', name)
    suffixes = r'\b(limited|pvt|private|ltd|inc|corp|co|gmbh|as|net|network)\b'
    name = re.sub(suffixes, '', name)
    return name.strip()

def calculate_match_score(row):
    input_name = clean_name(row['input_company_name'])
    candidate_name = clean_name(row['company_name'])
    legal_name = clean_name(row['company_legal_names'])
    
    score_name = SequenceMatcher(None, input_name, candidate_name).ratio() * 100
    score_legal = SequenceMatcher(None, input_name, legal_name).ratio() * 100
    best_text_score = max(score_name, score_legal)
    
    # Geographic check
    if str(row['input_main_country_code']).strip() == str(row['main_country_code']).strip():
        geo_modifier = 1.0
    else:
        geo_modifier = 0.5 
        
    final_score = best_text_score * geo_modifier
    
    # Website domain bonus
    domain = str(row['website_domain']).lower()
    if input_name.replace(" ", "") in domain and pd.notna(row['website_domain']):
        final_score += 10
        
    return min(final_score, 100)

# Run calculations
df['match_confidence_score'] = df.apply(calculate_match_score, axis=1)
best_matches = df.loc[df.groupby('input_row_key')['match_confidence_score'].idxmax()].copy()

# Add Curation Logic
best_matches['status'] = best_matches['match_confidence_score'].apply(
    lambda x: 'Auto-Accepted' if x >= 90 else ('Manual-Review' if x >= 50 else 'Reject')
)

# Keep only the important columns
columns_to_keep = [
    'input_company_name', 'company_name', 'match_confidence_score', 'status', 
    'website_domain', 'main_country'
]
curated_df = best_matches[columns_to_keep].copy()

# Final Output
curated_df.to_csv("Curated_Supplier_Master.csv", index=False)
print("Success! Curated_Supplier_Master.csv has been created.")