window.addEventListener('DOMContentLoaded', () => {
  // $('.dropdown-toggle').dropdown()
   // ---------------- Навыки ---------------- //
   const skillbar = document.querySelectorAll(".skillbar")
   const triggerBottom = window.innerHeight / 5 * 4
   const box = document.querySelector("#section_skills")

   if(box != null) {
    window.addEventListener('scroll', checkBoxes)
    checkBoxes()
   }

   function checkBoxes() {
    const boxTop = box.getBoundingClientRect().top
    if(boxTop < triggerBottom) {
      window.removeEventListener('scroll', checkBoxes)
      skillbar.forEach(element => {
        const skillbarBar = element.querySelector(".skillbar-bar")
        const dataPercent = +element.getAttribute('data-percent')
        let counter = 0
        const updateCounter = () => {
          if(counter < dataPercent) {
            counter = counter + 0.5
            skillbarBar.style.width = counter + '%';
            setTimeout(updateCounter, 1)
          } else {
            skillbarBar.style.width = counter + '%';
          }
        }
        updateCounter()
      });
    }
   }
});   