var system = require('system');
var page   = require('webpage').create();
// system.args[0] is the filename, so system.args[1] is the first real argument
var url    = system.args[1];
// render the page, and run the callback function

page.onLoadFinished = function(){
    console.log(page.content); // actual page
    phantom.exit();
};

page.open(url, function () {
  // page.content is the source
  //~ console.log(page.content);
  //~ // need to call phantom.exit() to prevent from hanging
  //~ phantom.exit();
});
