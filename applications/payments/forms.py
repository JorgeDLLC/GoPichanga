# applications/payments/forms.py
from django import forms
from datetime import date

def luhn_ok(num: str) -> bool:
    digits = [int(d) for d in num if d.isdigit()]
    if len(digits) < 12: return False
    checksum, parity = 0, len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d = d*2 - (9 if d*2 > 9 else 0)
        checksum += d
    return checksum % 10 == 0

def brand_from_pan(num: str) -> str:
    n = ''.join(c for c in num if c.isdigit())
    if n.startswith('4'): return 'VISA'
    if n[:2] in {'51','52','53','54','55'}: return 'Mastercard'
    if n.startswith(('34','37')): return 'Amex'
    return 'Card'

class PaymentForm(forms.Form):
    holder_name = forms.CharField(label='Titular', max_length=120)
    card_number = forms.CharField(label='Número de tarjeta', min_length=12, max_length=23)
    exp_month   = forms.IntegerField(label='Mes', min_value=1, max_value=12)
    exp_year    = forms.IntegerField(label='Año', min_value=date.today().year, max_value=date.today().year+15)
    cvv         = forms.CharField(label='CVV', min_length=3, max_length=4)

    def clean_card_number(self):
        num = self.cleaned_data['card_number'].replace(' ', '').replace('-', '')
        if not luhn_ok(num):
            raise forms.ValidationError("Tarjeta inválida (Luhn).")
        return num

    def clean(self):
        cleaned = super().clean()
        m, y = cleaned.get('exp_month'), cleaned.get('exp_year')
        if m and y:
            today = date.today()
            if (y, m) < (today.year, today.month):
                self.add_error('exp_year', 'Tarjeta vencida.')
        return cleaned

    def card_last4(self):
        return self.cleaned_data.get('card_number', '')[-4:]

    def card_brand(self):
        return brand_from_pan(self.cleaned_data.get('card_number', ''))
