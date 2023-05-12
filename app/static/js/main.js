document.addEventListener("DOMContentLoaded", function(event) {
  tippy('#tenureInformation', {
        content: "The length of time that a customer has been associated with you (in months)",
    });
  tippy('#partnerInformation', {
        content: "Does your customer also have a partner that has a contract with you",
    });
  tippy('#dependantsInformation', {
        content: "Are there individuals who rely on the primary account holder for their services.",
    });

 /*tippy('#servicesInformation', {
        content: "Is there any another additional monthly paid service that the customer has subscribed to",
    });*/

    // Get the query string parameters from the current URL
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has("prediction")) {
      if (urlParams.get("prediction") == 0)
        // The "my_variable" parameter is set, do something...
        Swal.fire({
        title: 'Prediction',
        text: 'Your client will not churn',
        icon: 'info',
        confirmButtonText: 'Ok'
        }).then(() => {window.location = "/"})
      else
        Swal.fire({
        title: 'Prediction',
        text: 'Your client will churn',
        icon: 'info',
        confirmButtonText: 'Ok'
        }).then(() => {window.location = "/"})
    }
});

function checkfile(sender) {
    let validExts = new Array(".xlsx", ".xls", ".csv");
    let fileExt = sender.value;
    fileExt = fileExt.substring(fileExt.lastIndexOf('.'));
    if (validExts.indexOf(fileExt) < 0) {
      alert("Invalid file selected, valid files are of " +
               validExts.toString() + " types.");
      return false;
    }
    else return true;
}