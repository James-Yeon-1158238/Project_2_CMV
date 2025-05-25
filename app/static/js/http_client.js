/**
 * Extends the Promise prototype to handle different HTTP response statuses.
 * These methods allow for handling specific HTTP error or success cases in a streamlined way.
 */

/**
 * Handles the case where a 400 Bad Request response is received.
 * It allows a callback to be executed when the response status is 400 (Bad Request).
 * 
 * @param {function} callback - The function to be called with the response data when the status is 400.
 * @returns {Promise} - The promise chain continues after handling the Bad Request response.
 */
Promise.prototype.onBadRequest = async function(callback) {
    return this.then((response) => {
        if (response.status === 400) {
            return response.json().then((data) => {
                callback(data);
                return data;
            });
        }
        return response;
    });
};

/**
 * Handles the case where a 200 OK response is received.
 * It allows a callback to be executed when the response status is 200 (OK).
 * 
 * @param {function} callback - The function to be called with the response data when the status is 200.
 * @returns {Promise} - The promise chain continues after handling the successful response.
 */
Promise.prototype.onSuccess = async function(callback) {
    return this.then((response) => {
        if (response.status === 200) {
            return response.json().then((data) => {
                callback(data);
                return data;
            });
        }
        return response;
    });
};

/**
 * Handles the case where a 401 Unauthorized response is received.
 * Redirects the user to the login page with the error message if the response status is 401.
 * 
 * @param {function} callback - This parameter is unused but kept for consistency in the function signature.
 * @returns {Promise} - The promise chain continues after handling the Unauthorized response.
 */
Promise.prototype.onUnauthorized = async function(callback) {
    return this.then((response) => {
        if (response.status === 401) {
            response.json().then((data) => {
                const message = data['err'];
                const redirectUrl = "/login";
                window.location.href = redirectUrl;
            });
        }
        return response;
    });
};

/**
 * Handles the case where a 403 Forbidden response is received.
 * It allows a callback to be executed when the response status is 403 (Forbidden).
 * 
 * @param {function} callback - The function to be called with the response data when the status is 403.
 * @returns {Promise} - The promise chain continues after handling the Forbidden response.
 */
Promise.prototype.onNotAllowed = async function(callback) {
    return this.then((response) => {
        if (response.status === 405) {
            return response.json().then((data) => {
                callback(data);
                return data;
            });
        }
        return response;
    });
};

/**
 * Fetches data from a URL using the Fetch API with additional options for credentials handling.
 * Provides the foundation for all HTTP requests (GET, POST, etc.).
 * 
 * @param {string} url - The URL to fetch data from.
 * @param {object} options - The options to pass to the Fetch API (optional).
 * @returns {Promise} - A Promise that resolves to the fetch response.
 */
async function dataFetcher(url, options = {}) {
    // Set default options for the fetch request
    const defaultOptions = {
        credentials: "include" // Include credentials (cookies, etc.) in cross-origin requests
    };
    const finalOptions = { ...defaultOptions, ...options }; // Merge the options with the defaults

    // Perform the fetch request and return the response
    return fetch(url, finalOptions)
        .then((response) => {
            return response; // Return the response for further handling
        }).onUnauthorized(data => {

        }).catch((err) => {
            console.error("Error sending request:", err); // Log any errors encountered during the fetch
        });
}

/**
 * A helper function for making POST requests with form data (`application/x-www-form-urlencoded` content type).
 * Uses the `dataFetcher` function to send form submissions.
 * 
 * @param {string} url - The URL to submit the form data to.
 * @param {object} options - The options to pass to the Fetch API (optional).
 * @returns {Promise} - A Promise that resolves to the fetch response.
 */
async function formFetch(url, options = {}) {
    // Call the dataFetcher function with the necessary options and headers for form submission
    return dataFetcher(url, {
        ...options,
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded" // Specify content type for form data
        }
    });
}

/**
 * A helper function for making GET requests to fetch data.
 * Uses the `dataFetcher` function with a GET method to retrieve data from the given URL.
 * 
 * @param {string} url - The URL to fetch data from.
 * @param {object} options - The options to pass to the Fetch API (optional).
 * @returns {Promise} - A Promise that resolves to the fetch response.
 */
async function getFetch(url, options = {}) {
    // Call the dataFetcher function with the necessary options and headers for form submission
    return dataFetcher(url, {
        ...options,
        method: "GET"
    });
}