javascript
// Client-side search functionality
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const suggestionsContainer = document.getElementById('suggestions-container');
    let debounceTimer;

    // Debounce function to limit API calls while typing
    const debounce = (func, delay) => {
        return (...args) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => func.apply(this, args), delay);
        };
    };

    // Fetch autocomplete suggestions from API
    const fetchSuggestions = async (query) => {
        try {
            const response = await fetch(`/api/search/autocomplete?q=${encodeURIComponent(query)}`);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            return data.suggestions;
        } catch (error) {
            console.error('Error fetching suggestions:', error);
            return [];
        }
    };

    // Render suggestions in the dropdown
    const renderSuggestions = (suggestions) => {
        suggestionsContainer.innerHTML = '';
        if (suggestions.length === 0) {
            suggestionsContainer.style.display = 'none';
            return;
        }

        suggestions.forEach(suggestion => {
            const div = document.createElement('div');
            div.className = 'suggestion-item';
            div.textContent = suggestion;
            div.addEventListener('click', () => {
                searchInput.value = suggestion;
                suggestionsContainer.style.display = 'none';
                submitSearch(suggestion);
            });
            suggestionsContainer.appendChild(div);
        });
        suggestionsContainer.style.display = 'block';
    };

    // Submit search query
    const submitSearch = async (query) => {
        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });
            if (!response.ok) {
                throw new Error('Search request failed');
            }
            const results = await response.json();
            displayResults(results);
        } catch (error) {
            console.error('Error submitting search:', error);
        }
    };

    // Display search results
    const displayResults = (results) => {
        const resultsContainer = document.getElementById('search-results');
        resultsContainer.innerHTML = '';
        
        results.forEach(result => {
            const resultDiv = document.createElement('div');
            resultDiv.className = 'search-result';
            resultDiv.innerHTML = `
                <h3>${result.title}</h3>
                <p>${result.description}</p>
                <div class="feedback-buttons">
                    <button onclick="submitFeedback('${result.id}', true)">👍</button>
                    <button onclick="submitFeedback('${result.id}', false)">👎</button>
                </div>
            `;
            resultsContainer.appendChild(resultDiv);
        });
    };

    // Submit user feedback
    window.submitFeedback = async (resultId, isPositive) => {
        try {
            await fetch('/api/search/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    result_id: resultId,
                    is_positive: isPositive
                })
            });
        } catch (error) {
            console.error('Error submitting feedback:', error);
        }
    };

    // Event listeners
    searchInput.addEventListener('input', debounce(async (e) => {
        const query = e.target.value.trim();
        if (query.length >= 2) {
            const suggestions = await fetchSuggestions(query);
            renderSuggestions(suggestions);
        } else {
            suggestionsContainer.style.display = 'none';
        }
    }, 300));

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            submitSearch(searchInput.value.trim());
            suggestionsContainer.style.display = 'none';
        }
    });

    // Close suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (!suggestionsContainer.contains(e.target) && e.target !== searchInput) {
            suggestionsContainer.style.display = 'none';
        }
    });
});
