function removeRange(button) {
  const rangeInput = button.parentElement;
  const container = document.getElementById("rangesContainer");

  // Don't remove if it's the last range
  if (container.querySelectorAll(".range-input").length > 1) {
    rangeInput.remove();
  } else {
    // If it's the last range, just clear the inputs
    rangeInput.querySelector(".start-page").value = "";
    rangeInput.querySelector(".end-page").value = "";
  }
}

document.getElementById("addRange").addEventListener("click", () => {
  const container = document.getElementById("rangesContainer");
  const newRange = document.createElement("div");
  newRange.className = "range-input flex space-x-2";
  newRange.innerHTML = `
            <input type="number" 
                   placeholder="Start" 
                   min="1" 
                   class="start-page w-1/3 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                   required>
            <input type="number" 
                   placeholder="End" 
                   min="1" 
                   class="end-page w-1/3 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                   required>
            <button type="button" 
                    class="remove-range w-1/3 px-3 py-2 border border-transparent text-sm font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                    onclick="removeRange(this)">
                Remove
            </button>
        `;
  container.appendChild(newRange);
});

document.getElementById("splitForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const errorDiv = document.getElementById("error");
  const loadingDiv = document.getElementById("loading");
  errorDiv.classList.add("hidden");
  loadingDiv.classList.remove("hidden");

  // Collect all ranges
  const ranges = [];
  document.querySelectorAll(".range-input").forEach((range) => {
    const start = range.querySelector(".start-page").value;
    const end = range.querySelector(".end-page").value;
    if (start && end) {
      ranges.push(`${start}-${end}`);
    }
  });

  const formData = new FormData();
  formData.append("pdf_file", document.getElementById("pdfFile").files[0]);
  formData.append("ranges", ranges.join(","));

  try {
    const response = await fetch("/split", {
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      // Trigger file download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.style.display = "none";
      a.href = url;
      a.download = "split_pdfs.zip";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } else {
      const data = await response.json();
      throw new Error(data.error || "Failed to split PDF");
    }
  } catch (error) {
    errorDiv.textContent = error.message;
    errorDiv.classList.remove("hidden");
  } finally {
    loadingDiv.classList.add("hidden");
  }
});
