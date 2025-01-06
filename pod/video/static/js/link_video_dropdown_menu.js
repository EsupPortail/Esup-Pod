function confirmDuplication(event, url, confirmationText) {
  if (confirm(confirmationText)) {
    window.location.href = url;
  } else {
    event.preventDefault();
    return false;
  }
}