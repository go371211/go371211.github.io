// list group for navbar
addClassToChildren(document, '.sidebar-nav', 'list-group');
const sidebarListGroups = document.querySelectorAll('.sidebar-nav.list-group');
sidebarListGroups.forEach(listGroup => {
    addClassToChildren(listGroup, 'li', 'list-group-item');
    addClassToChildren(listGroup, 'li', 'list-group-item-action');
});


// highlight current page
const sidebarLinks = document.querySelectorAll('.sidebar-nav a');
sidebarLinks.forEach(sidebarLink => {
    let sidebarLinkURL = sidebarLink.getAttribute('href').split('?')[0];
    let currentURL = document.URL.split('?')[0];
    if (currentURL.endsWith(sidebarLinkURL)) {
        sidebarLink.parentElement.classList.add('active');
    }
});


// list group for main content
addClassToChildren(document, '.col-sm-10 ul:not([list-group="off"])', 'list-group');
const mainContentListGroups = document.querySelectorAll('.col-sm-10 .list-group');
mainContentListGroups.forEach(listGroup => {
    addClassToChildren(listGroup, 'li', 'list-group-item');
});


// button for staff button
const staffButtons = document.querySelectorAll('.staff-button');
staffButtons.forEach(staffButton => {
    staffButton.classList.add('btn');
    staffButton.classList.add('btn-sm');
    staffButton.classList.add('btn-primary');
});

// form group for form
const forms = document.querySelectorAll('form');
forms.forEach(form => {
    form.classList.add('form-group')
    addClassToChildren(form, 'input', 'form-control');
});


function addClassToChildren(parent, child, klass) {
    let children = parent.querySelectorAll(child);
    children.forEach(child => {
        child.classList.add(klass);
    });
}