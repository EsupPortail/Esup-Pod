from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from .models import Hyperlink
from .forms import HyperlinkForm


@csrf_protect
@login_required(redirect_field_name="referrer")
def manage_hyperlinks(request):
    """Display all hyperlinks."""
    hyperlinks = Hyperlink.objects.all()
    return render(
        request, "hyperlinks/manage_hyperlinks.html", {"hyperlinks": hyperlinks}
    )


@csrf_protect
@login_required(redirect_field_name="referrer")
def add_hyperlink(request):
    """Add a new hyperlink."""
    if request.method == "POST":
        form = HyperlinkForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("hyperlinks:manage_hyperlinks")
    else:
        form = HyperlinkForm()
    return render(request, "hyperlinks/add_hyperlink.html", {"form": form})


@csrf_protect
@login_required(redirect_field_name="referrer")
def edit_hyperlink(request, hyperlink_id):
    """Edit an existing hyperlink."""
    hyperlink = get_object_or_404(Hyperlink, id=hyperlink_id)
    if request.method == "POST":
        form = HyperlinkForm(request.POST, instance=hyperlink)
        if form.is_valid():
            form.save()
            return redirect("hyperlinks:manage_hyperlinks")
    else:
        form = HyperlinkForm(instance=hyperlink)
    return render(
        request, "hyperlinks/edit_hyperlink.html", {"form": form, "hyperlink": hyperlink}
    )


@csrf_protect
@login_required(redirect_field_name="referrer")
def delete_hyperlink(request, hyperlink_id):
    """Delete an existing hyperlink."""
    hyperlink = get_object_or_404(Hyperlink, id=hyperlink_id)
    if request.method == "POST":
        hyperlink.delete()
        return redirect("hyperlinks:manage_hyperlinks")
    return render(request, "hyperlinks/delete_hyperlink.html", {"hyperlink": hyperlink})
