document.addEventListener("DOMContentLoaded", function () {
    // Clear radio button selections
    var radioButtons = document.querySelectorAll('input[type="radio"]');
    radioButtons.forEach(function (radio) {
        radio.checked = false;
    });

    var textFields = document.querySelectorAll('input[type="text"]');
    textFields.forEach(function (textField) {
        textField.value = "";
    });
});

