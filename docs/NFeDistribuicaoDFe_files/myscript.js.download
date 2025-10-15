var navbar;
var sticky;

window.onload = function() {
  navbar = document.getElementById("barra_superior");
  sticky = navbar.offsetTop;
  myFunction()

};
window.onscroll = function() {
  myFunction()
};




function myFunction() {


  if (window.pageYOffset >= sticky) {
    navbar.classList.add("sticky");
  } else {
    navbar.classList.remove("sticky");
  }

  var element = document.getElementById("barra_superior");
  var leftmenu = document.getElementById("indice");
  elemRect = element.getBoundingClientRect();
  leftmenu.style.paddingTop = elemRect.bottom + "px";
}



function menu() {
  var fechar = document.getElementById("menu_esq");
  if (fechar.style.display != "none") {
    fechar.style.display = "none";
  //  var parte_maior = document.getElementById("principal");
    document.getElementById("botao_menu").classList.remove("active");
  //  parte_maior.style.paddingLeft = "10px";
  } else {
    fechar.style.display = "block";
  //  var parte_maior = document.getElementById("principal");
  //  parte_maior.style.paddingLeft = "320px";
    document.getElementById("botao_menu").classList.add("active");

  }
}

function pesquisa() {

  var input, filter, table, tr, td, i, txtValue;
  input = document.getElementById("myInput");
  filter = input.value.toUpperCase();
  table = document.getElementById("indice");
  tr = table.getElementsByTagName('a');
  breakline = table.getElementsByTagName('br');


  // Loop through all table rows, and hide those who don't match the search query
  for (i = 0; i < tr.length; i++) {
    if (tr[i]) {
      txtValue = tr[i].textContent || tr[i].innerText;
      if (txtValue.toUpperCase().indexOf(filter) > -1) {
        tr[i].style.display = "";
        breakline[(i * 2 + 1)].style.display = "";
        breakline[(i * 2)].style.display = "";
      } else {
        tr[i].style.display = "none";
        breakline[(i * 2 + 1)].style.display = "none"; //para cada tag escondida, tenho duas tags br, uma interna e outra externa. Logo, a tag br que eu quero esconder com essa função é sempre dada por i*2+1
        breakline[(i * 2)].style.display = "none"; //para cada tag escondida, tenho duas tags br, uma interna e outra externa. Logo, a tag br que eu quero esconder com essa função é sempre dada por i*2+1
      }
    }
  }
}

function meiodatela(id_elemento) {
  //console.log("opa, esta querendo que eu va ate o elemento   " + id_elemento);
  var elmnt = document.getElementById(id_elemento);
  posicao = elmnt.offsetTop - 100;
  console.log("peguei a posicao dele, ta em   " + posicao);
  menu();//chamo o menu para que ele seja fechado caso eu tenha clicado em algum link
  window.scrollTo(0, posicao);
}
