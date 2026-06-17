/**
 * Placeholder client script for customer menu UI interactions.
 * Cart and ordering logic will be implemented in the orders app.
 */
document.addEventListener("DOMContentLoaded", function () {
    const filterPills = document.querySelectorAll(".filter-pill");
    const menuItems = document.querySelectorAll(".menu-item");
    const cartBtn = document.getElementById("cart-btn");
    let cartCount = 0;

    filterPills.forEach(function (pill) {
        pill.addEventListener("click", function () {
            const category = pill.dataset.category;

            filterPills.forEach(function (p) {
                p.classList.remove("active");
            });
            pill.classList.add("active");

            menuItems.forEach(function (item) {
                const itemCategory = item.dataset.category;
                const show = category === "all" || itemCategory === category;
                item.classList.toggle("hidden", !show);
            });
        });
    });

    document.querySelectorAll(".btn-add").forEach(function (btn) {
        btn.addEventListener("click", function () {
            cartCount += 1;
            if (cartBtn) {
                cartBtn.textContent = "Cart · " + cartCount;
            }
        });
    });
});
