"""Parse an untrusted PDF in a bounded child process."""
import json,re,sys

def extract(path):
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024));resource.setrlimit(resource.RLIMIT_CPU,(15,15))
    except ImportError:pass
    from pypdf import PdfReader
    reader=PdfReader(path,strict=True)
    if reader.is_encrypted:raise ValueError('Password-protected PDFs are not supported')
    if len(reader.pages)>40:raise ValueError('Upload a PDF with 40 pages or fewer')
    result=[]
    for number,page in enumerate(reader.pages,1):
        text=page.extract_text() or ''
        if len(text)>10000:raise ValueError('Page contains too much text; split this document')
        candidates=[];pattern=r'(?:AED|Dhs?\.?|د\.إ)\s*([\d,]+(?:\.\d{1,2})?)|([\d,]+(?:\.\d{1,2})?)\s*(?:AED|Dhs?\.?)'
        for match in list(re.finditer(pattern,text,re.I))[:100]:
            amount=(match.group(1) or match.group(2)).replace(',','')
            if float(amount)>10000000:continue
            candidates.append({'amount':f'{float(amount):.2f}','excerpt':text[max(0,match.start()-65):min(len(text),match.end()+65)],'page':number})
        result.append({'page':number,'text':text,'candidates':candidates})
    return result
if __name__=='__main__':
    try:print(json.dumps(extract(sys.argv[1])))
    except Exception as e:print(str(e)[:250],file=sys.stderr);sys.exit(1)
