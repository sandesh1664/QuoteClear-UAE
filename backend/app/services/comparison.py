from decimal import Decimal,ROUND_HALF_UP
from ..models import Quote,LineItem

def fils(value): return int((Decimal(str(value))*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
def money(value:int): return f'{Decimal(value)/100:.2f}'

def analyze(quote:Quote,items:list[LineItem])->dict:
    subtotal=sum((i.amount or 0)*i.quantity for i in items if i.pricing=='fixed')
    flags=[]
    unknown=[i.label for i in items if i.pricing=='unknown']
    unreviewed=[i.label for i in items if not i.reviewed]
    if unknown: flags.append({'code':'unknown_cost','label':'Unpriced items','detail':', '.join(unknown),'blocks_total':True})
    if unreviewed: flags.append({'code':'unreviewed','label':'Review required','detail':', '.join(unreviewed),'blocks_total':True})
    if quote.tax_mode=='unspecified': flags.append({'code':'tax','label':'Tax treatment unspecified','detail':'Ask whether tax is included or additional.','blocks_total':True})
    for field,label in [('warranty_days','Warranty'),('completion_days','Completion time')]:
        if getattr(quote,field) is None: flags.append({'code':field,'label':label+' not specified','detail':'Ask the provider to confirm in writing.','blocks_total':False})
    if not quote.exclusions: flags.append({'code':'exclusions','label':'Exclusions not specified','detail':'Confirm what is outside the quoted scope.','blocks_total':False})
    if not quote.valid_until: flags.append({'code':'validity','label':'Quote validity not specified','detail':'Ask how long this price remains valid.','blocks_total':False})
    tax=int((Decimal(subtotal)*Decimal(quote.tax_rate)/10000).quantize(Decimal('1'),rounding=ROUND_HALF_UP)) if quote.tax_mode=='excluded' else 0
    confirmed=not any(f['blocks_total'] for f in flags)
    return {'known_subtotal':money(subtotal),'additional_tax':money(tax) if quote.tax_mode!='unspecified' else None,'known_total':money(subtotal+tax),'confirmed_total':money(subtotal+tax) if confirmed else None,'flags':flags,'reviewed_count':sum(i.reviewed for i in items),'item_count':len(items)}

def clarification(provider:str,analysis:dict)->str:
    lines=[f'Hello {provider}, thank you for the quotation. Before I confirm, could you please clarify:']
    questions={'unknown_cost':'The price for each unpriced item: ','unreviewed':'The quoted amounts for: ','tax':'Whether the total includes tax or tax is additional.','warranty_days':'The warranty period and what it covers.','completion_days':'The expected start and completion time.','exclusions':'Any exclusions, extra charges or approval requirements.','validity':'How long this quotation is valid.'}
    for f in analysis['flags']:
        q=questions[f['code']]+(f['detail'] if f['code'] in ('unknown_cost','unreviewed') else '')
        lines.append(f'{len(lines)}. {q}')
    if len(lines)==1: lines.append('Please confirm that the scope and total shown are final, and that additional work will require my approval.')
    return '\n\n'.join(lines)+'\n\nPlease send the confirmed details in writing. Thank you.'
