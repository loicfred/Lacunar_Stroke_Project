document.getElementById("strokeForm").addEventListener("submit", function (e) {
    e.preventDefault();

    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());

    console.log("Form Data:", data);

    document.getElementById("result").textContent =
        "Form submitted successfully (prediction logic not yet connected)";
});

// Logout Button
document.getElementById("logoutBtn").addEventListener("click", function () {
    alert("You have been logged out.");
});
