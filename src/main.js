document.addEventListener("DOMContentLoaded", () => {
  const suggestionsData = [
    "Математика",
    "Математика – Основи",
    "Физика",
    "Химия",
    "Български език",
    "История",
    "Английски език",
    "География",
    "Информатика",
    "Програмиране на C++"
  ];

  const searchInput = document.getElementById("searchInput");
  const suggestionsList = document.getElementById("suggestions");

  searchInput.addEventListener("input", () => {
    const value = searchInput.value.toLowerCase();
    suggestionsList.innerHTML = "";

    if (value) {
      const filtered = suggestionsData.filter(item => item.toLowerCase().includes(value));
      filtered.forEach(item => {
        const li = document.createElement("li");
        li.textContent = item;
        li.addEventListener("click", () => {
          searchInput.value = item;
          suggestionsList.innerHTML = "";
        });
        suggestionsList.appendChild(li);
      });
    }
  });

  document.addEventListener("click", (e) => {
    if (!e.target.closest(".search-wrapper")) {
      suggestionsList.innerHTML = "";
    }
  });

  function goToTests() {
    window.location.href = "tests.html";
  }
});
