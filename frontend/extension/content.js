const allParagraphs = document.querySelectorAll("p");
let text = Array.from(allParagraphs).map(p => p.innerText).join(" ");

if(allParagraphs){
  console.log(text);
}