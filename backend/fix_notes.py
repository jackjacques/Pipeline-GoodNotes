import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from supabase_client import SupabaseHelper

s = SupabaseHelper()

note_id = "c8d62290-32cd-4dbc-b45f-0f7475a3889a"
res = s.client.table('notes').select('full_transcription, summary').eq('id', note_id).execute()
if res.data:
    txt = res.data[0]['full_transcription']
    summ = res.data[0]['summary']
    
    # Clean up tab characters that preceded 'ext{' -> '\text{'
    txt = txt.replace('\text{', '\\text{').replace('\text', '\\text').replace('\t', '\\t')
    txt = txt.replace('\\text', '\\text') # ensure double slash
    txt = txt.replace('zsh.3%', '0.3%')
    txt = txt.replace('36914', '$$')
    
    # Fix in summary
    summ = summ.replace('\text{', '\\text{').replace('\text', '\\text').replace('\t', '\\t')
    summ = summ.replace('36914', '$$')
    
    s.client.table('notes').update({
        'full_transcription': txt,
        'summary': summ
    }).eq('id', note_id).execute()
    print("Fixed note strings cleanly!")
