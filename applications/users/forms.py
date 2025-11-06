from django import forms

class RegularCreateForm(forms.Form):
    nombre = forms.CharField(max_length=150, label="Nombre completo")
    email = forms.EmailField(label="Correo")
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")
    telefono = forms.CharField(max_length=15, required=False, label="Teléfono")
    fecha_nacimiento = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    direccion = forms.CharField(max_length=255, required=False)

    def clean_nombre(self):
        return self.cleaned_data["nombre"].strip()

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

class LoginForm(forms.Form):
    email = forms.EmailField(label="Correo")
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")