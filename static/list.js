let socket;

const readylist = document.getElementById("readylist");
const waitlist = document.getElementById("waitlist");
const okno = document.getElementById("okno");
const pictures = document.getElementById("splideList");
var orderOkno = document.getElementById("orderokno");
const audio = new Audio("/static/order_ready.mp3");

function addToReadyList(orderNumber) {
  var order = document.createElement("li");
  order.appendChild(document.createTextNode(orderNumber));
  order.className = "ready";
  readylist.appendChild(order);
}

function addToWaitList(orderNumber) {
  var order = document.createElement("li");
  order.appendChild(document.createTextNode(orderNumber));
  order.className = "wait";
  waitlist.appendChild(order);
}

function connectToWS() {
  const connect = document.getElementById("connect");

  socket = new WebSocket("ws://" + window.location.hostname + ":8000/ws");
  socket.onmessage = function (event) {
    while (readylist.firstChild) readylist.firstChild.remove();
    while (waitlist.firstChild) waitlist.firstChild.remove();

    var json = JSON.parse(event.data);
    for (const orderNumber of json["readylist"]) {
      addToReadyList(orderNumber["orderNumber"]);
    }
    for (const orderNumber of json["waitlistOrders"]) {
      addToWaitList(orderNumber["orderNumber"]);
    }
    for (const orderNumber of json["inProgresslistOrders"]) {
      addToWaitList(orderNumber["orderNumber"]);
    }

    if (json["pictures"].length > 0) {
      while (pictures.firstChild) pictures.firstChild.remove();

      for (const picture of json["pictures"]) {
        var image = document.createElement("li");
        image.className = "slide splide__slide";

        var img = document.createElement("img");
        img.src = picture["src"];
        img.alt = picture["alt"];

        image.appendChild(img);

        pictures.appendChild(image);
      }

      var splide = new Splide('.splide', {
        type: 'loop',
        autoplay: true,
        interval: 10000,
        pauseOnFocus: false,
        arrows: false,
        pagination: false,
      })
      splide.mount();
      splide.Components.Autoplay.play();
    }

    if (json["freshlist"].length > 0) {
      audio.play();
    }

    for (const orderNumber of json["freshlist"]) {
      orderOkno.textContent = orderNumber;
      jQuery("#okno")
        .css("display", "flex")
        .fadeIn(300)
        .delay(3000)
        .fadeOut(300);
    }
  };
}

function connectToServer() {
  connectToWS();
  jQuery("#connectokno").fadeOut();
}

$(document).ready(function () {
  //connectToWS();
  // Создаем две переменные с названиями месяцев и названиями дней.
  var monthNames = [
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
  ];
  var dayNames = [
    "Воскресенье",
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
  ];

  setInterval( function() {
    var newDate = new Date();
    
    $("#date").html(
      dayNames[newDate.getDay()] +
      " " +
      newDate.getDate() +
      " " +
      monthNames[newDate.getMonth()] +
      " " +
      newDate.getFullYear()
    );
  }, 1000);

  setInterval(function () {
    // Создаем объект newDate() и показывает минуты
    var minutes = new Date().getMinutes();
    // Добавляем ноль в начало цифры, которые до 10
    $("#min").html((minutes < 10 ? "0" : "") + minutes);
  }, 1000);

  setInterval(function () {
    // Создаем объект newDate() и показывает часы
    var hours = new Date().getHours();
    // Добавляем ноль в начало цифры, которые до 10
    $("#hours").html((hours < 10 ? "0" : "") + hours);
  }, 1000);
});
