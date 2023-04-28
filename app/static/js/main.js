document.addEventListener("DOMContentLoaded", function(event) {
  tippy('#tenureInformation', {
        content: "The length of time that a customer has been associated with you (in months)",
    });
  tippy('#partnerInformation', {
        content: "Does your customer also have a partner that has a contract with you",
    });
  tippy('#dependantsInformation', {
        content: "Are there individuals who rely on the primary account holder for their telecom services.",
    });
  tippy('#servicesInformation', {
        content: "Is there any another additional monthly paid service that the customer has subscribed to",
    });
});