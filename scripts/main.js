let myImage=document.querySelector('img');
let myHeading=document.querySelector('h1');
let myButton=document.querySelector('button');

//圖片變換
myImage.onclick=function() {
  src=myImage.getAttribute('src');
  if (src==='images/firefox.png') {
    myImage.setAttribute('src','images/firefox2.png');
  } else {
    myImage.setAttribute('src','images/firefox.png');
  }
}

//改變使用者
let setName=function() {
  let name=prompt('Please enter your name:');
  if (!name || name===null) {
    setName();
  } else {
    localStorage.setItem('name',name);
    myHeading.textContent='Welcome! '+name;
  }
}

//初始化歡迎訊息
if (!localStorage.getItem('name')) {
  setName();
} else {
  myHeading.textContent='Welcome! '+localStorage.getItem('name');
}

//按鈕
myButton.onclick=function() {
  setName();
}
