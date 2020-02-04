const socket = io();

$(() => {
    console.log('Page loaded');


    //*************************************************************** GUI
    $('#navbar').on('click', 'a', (e) => {
        if (e.target.id == 'navbar-register') {
            if ($('#register').is(':visible')) {
                $('#register').hide();
            } else {
                $('#register').show();
            }
        }
    });
});
