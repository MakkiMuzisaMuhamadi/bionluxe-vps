from django import forms
from .models import Products, Categories, Brands, SlideImage, ProductImage

# Bootstrap 4 classes
BOOTSTRAP_INPUT = "form-control"
BOOTSTRAP_SELECT = "form-control"
BOOTSTRAP_TEXTAREA = "form-control"
BOOTSTRAP_CHECK = "form-check-input"
BOOTSTRAP_FILE = "form-control"


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class BootstrapFormMixin:
    """
    Apply Bootstrap 4 classes consistently to all form fields.
    This fixes plain HTML-looking inputs/selects in the dashboard.
    """

    def apply_bootstrap(self):
        for name, field in self.fields.items():
            widget = field.widget
            existing_classes = widget.attrs.get("class", "").split()

            # remove old bootstrap/select2 classes before re-applying
            remove_classes = {
                "form-control",
                "form-select",
                "form-check-input",
                "select2-field",
            }
            cleaned = [c for c in existing_classes if c not in remove_classes]

            # CHECKBOX
            if isinstance(widget, forms.CheckboxInput):
                css_classes = cleaned + [BOOTSTRAP_CHECK]

            # FILE INPUT
            elif isinstance(widget, (forms.ClearableFileInput, MultipleFileInput)):
                css_classes = cleaned + [BOOTSTRAP_FILE]
                widget.attrs.setdefault("accept", "image/*")

            # TEXTAREA
            elif isinstance(widget, forms.Textarea):
                css_classes = cleaned + [BOOTSTRAP_TEXTAREA]
                widget.attrs.setdefault("rows", 4)

            # DATE SELECT WIDGET
            elif isinstance(widget, forms.SelectDateWidget):
                css_classes = cleaned + [BOOTSTRAP_SELECT]

            # SELECT
            elif isinstance(widget, forms.Select):
                css_classes = cleaned + [BOOTSTRAP_SELECT]

            # EVERYTHING ELSE
            else:
                css_classes = cleaned + [BOOTSTRAP_INPUT]

            widget.attrs["class"] = " ".join(css_classes).strip()

            # common attrs
            if not isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("autocomplete", "off")

            if isinstance(widget, forms.DateInput):
                widget.attrs.setdefault("type", "date")

            if isinstance(
                widget,
                (
                    forms.TextInput,
                    forms.EmailInput,
                    forms.NumberInput,
                    forms.DateInput,
                    forms.URLInput,
                    forms.PasswordInput,
                ),
            ):
                widget.attrs.setdefault("placeholder", field.label)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class ProductForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Products
        fields = [
            "category",
            "brand",
            "product_name",
            "image",
            "price",
            "description",
            "discount_amount",
            "discount_percent",
            "topsales",
            "trending",
            "dryskinproducts",
            "oilyskin",
            "acneprone",
            "brightening",
            "antiaging",
            "sunscreen",
            "lightening",
            "is_out_of_stock",
        ]
        widgets = {
            "category": forms.Select(),
            "brand": forms.Select(),
            "product_name": forms.TextInput(attrs={"placeholder": "Enter product name"}),
            "image": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "price": forms.NumberInput(attrs={"placeholder": "Enter product price"}),

            "description": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Write product description"
            }),

            "discount_amount": forms.NumberInput(attrs={"placeholder": "Optional discount amount"}),
            "discount_percent": forms.NumberInput(attrs={"placeholder": "Optional discount percent"}),

            "topsales": forms.CheckboxInput(),
            "trending": forms.CheckboxInput(),
            "dryskinproducts": forms.CheckboxInput(),
            "oilyskin": forms.CheckboxInput(),
            "acneprone": forms.CheckboxInput(),
            "brightening": forms.CheckboxInput(),

            "antiaging": forms.CheckboxInput(),
            "sunscreen": forms.CheckboxInput(),
            "lightening": forms.CheckboxInput(),

            "is_out_of_stock": forms.CheckboxInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        discount_amount = cleaned_data.get("discount_amount")
        discount_percent = cleaned_data.get("discount_percent")

        if discount_amount and discount_percent:
            raise forms.ValidationError(
                "Use either discount amount or discount percent, not both."
            )
        return cleaned_data
    
class ProductImageForm(BootstrapFormMixin, forms.Form):
    images = forms.FileField(
        required=False,
        label="Other Product Images / Gallery",
        widget=MultipleFileInput(
            attrs={
                "multiple": True,
                "accept": "image/*",
            }
        ),
        help_text="You can select multiple gallery images at once.",
    )


class CategoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Categories
        fields = ["name", "image"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Enter category name"}),
            "image": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }


class BrandForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Brands
        fields = ["name", "image"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Enter brand name"}),
            "image": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }


class SlideForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = SlideImage
        fields = ["title", "description", "image"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Enter slide title"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Enter slide description"}),
            "image": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }