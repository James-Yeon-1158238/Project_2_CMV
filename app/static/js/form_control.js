/**
 * Clears the error styles and adds a success border when the user starts typing in the input.
 * This function listens for an "input" event and applies the styles accordingly.
 * 
 * @param {string} selector - The CSS selector for the input element to apply the event listener.
 */
function clearErrorOnInput(selector) {
    const inputElement = document.querySelector(selector);
    if (!inputElement) return;
    inputElement.addEventListener("input", () => {
        inputElement.classList.remove('is-invalid', 'border-danger');
        inputElement.classList.add("border-success");
    });
}

/**
 * Checks if all elements in the provided list have valid values (non-empty).
 * If any field is empty, it applies error styles to the input and prevents submission.
 * 
 * @param {Array<string>} elements - An array of element IDs to check for validity.
 * @returns {boolean} - Returns `true` if all elements have values, otherwise `false`.
 */
function preSubmitCheck(elements) {
    let canSubmit = true;
    elements.forEach(element => {
        const input = document.getElementById(element);
        if (input.value.trim() === "") {
            input.classList.add('is-invalid', 'border-danger');
            canSubmit = false;
        }
    });
    return canSubmit;
}

/**
 * Validates the password and password confirmation fields to ensure they match.
 * Adds error styles if the fields are empty or do not match.
 * 
 * @param {string} password - The ID of the password input element.
 * @param {string} passwordConfirm - The ID of the password confirmation input element.
 * @returns {boolean} - Returns `true` if the passwords match and are not empty, otherwise `false`.
 */
function passwordConfirmCheck(password, passwordConfirm) {
    const pwd = document.getElementById(password);
    const confirm = document.getElementById(passwordConfirm);
    let canSubmit = true;
	if (pwd.value.trim() === "") {
        pwd.classList.add('is-invalid', 'border-danger');
        canSubmit = false;
    }
    if (confirm.value.trim() !== pwd.value.trim()) {
        confirm.classList.add('is-invalid', 'border-danger');
        canSubmit = false;
    }
    return canSubmit;
}

/**
 * Inserts an error message next to the input element and applies error styles.
 * 
 * @param {string} selector - The CSS selector for the input element.
 * @param {string} message - The error message to display.
 */
function insertErrorTip(selector, message) {
    const ipt = document.querySelector(selector);
    ipt.classList.add('is-invalid', 'border-danger');
    const invalidFeedback = ipt.nextElementSibling;
    invalidFeedback.textContent = message
}

/**
 * Disables the button and displays a loading spinner to indicate an ongoing process.
 * 
 * @param {HTMLElement} button - The button element to be disabled.
 */
function loadButton(button) {
    button.disabled = true;
    button.innerHTML = `<span class="spinner-border spinner-border-sm"></span>`;
}

/**
 * Restores the button to its original state, enabling it and setting the button text back to the provided HTML.
 * 
 * @param {HTMLElement} button - The button element to be restored.
 * @param {string} html - The original HTML content for the button (e.g., button text).
 */
function restoreButton(button, html) {
    button.disabled = false;
    button.innerHTML = html;
}

/**
 * Displays an error toast message to the user for a specified duration.
 * 
 * @param {string} errorMessage - The error message to display.
 * @param {number} timeout - The duration in milliseconds to show the toast.
 */
function showErrorToast(errorMessage, timeout) {
    const toastElement = document.getElementById('error-toast');
	const toastMessageElement = document.getElementById('error-toast-message');
	toastMessageElement.textContent = errorMessage;
	const toast = new bootstrap.Toast(toastElement);
	toast.show();
	setTimeout(() => {
        toast.hide();
    }, timeout); 
}

/**
 * Displays an informational toast message to the user for a specified duration.
 * 
 * @param {string} infoMessage - The informational message to display.
 * @param {number} timeout - The duration in milliseconds to show the toast.
 */
function showInfoToast(infoMessage, timeout) {
    const toastElement = document.getElementById('info-toast');
	const toastMessageElement = document.getElementById('info-toast-message');
	toastMessageElement.textContent = infoMessage;
	const toast = new bootstrap.Toast(toastElement);
	toast.show();
	setTimeout(() => {
        toast.hide();
    }, timeout); 
}

function formatDateToInput(dateString) {
    const parts = dateString.split('-');
    if (parts.length !== 3) return '';

    const [day, month, year] = parts;
    const parsed = new Date(`${year}-${month}-${day}`);

    if (isNaN(parsed)) return '';
    return parsed.toISOString().split('T')[0];
}

function formatDateTimeToInput(dateString) {
    if (!dateString || dateString === 'null') return '';
    const parsed = new Date(dateString);
    if (isNaN(parsed)) return '';

    const year = parsed.getFullYear();
    const month = String(parsed.getMonth() + 1).padStart(2, '0');
    const day = String(parsed.getDate()).padStart(2, '0');
    const hours = String(parsed.getHours()).padStart(2, '0');
    const minutes = String(parsed.getMinutes()).padStart(2, '0');

    return `${year}-${month}-${day}T${hours}:${minutes}`;
}