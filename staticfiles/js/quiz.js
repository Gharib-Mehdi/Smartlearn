document.addEventListener('DOMContentLoaded', () => {
  const choices = document.querySelectorAll('.sl-choice-item');
  const submitBtn = document.getElementById('submitBtn');
  const hiddenInput = document.getElementById('selected-choice');

  choices.forEach(choice => {
    choice.addEventListener('click', () => {
      choices.forEach(c => c.classList.remove('selected'));
      choice.classList.add('selected');
      if (hiddenInput) hiddenInput.value = choice.dataset.choiceId;
      if (submitBtn) submitBtn.disabled = false;
    });
  });

  choices.forEach(choice => {
    choice.setAttribute('tabindex', '0');
    choice.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        choice.click();
      }
    });
  });
});
