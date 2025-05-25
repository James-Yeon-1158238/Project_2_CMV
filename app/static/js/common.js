const DETAULT_AVATOR = '../static/profile/default.png'

class Admin {

    constructor(value) {
        this.value = value;
    }

    handleAvatorBadge(badge) {
        badge.classList.add("text-bg-primary");
        badge.innerHTML = this.value;
    }

    handleProfileBadge(button) {
        button.classList.add("btn-outline-primary");
        button.innerHTML = this.value;
    }

}

class Helper {

    constructor(value) {
        this.value = value;
    }

    handleAvatorBadge(badge) {
        badge.classList.add("text-bg-warning");
        badge.innerHTML = this.value;
    }

    handleProfileBadge(button) {
        button.classList.add("btn-outline-warning");
        button.innerHTML = this.value;
    }

}

class Visitor {

    constructor(value) {
        this.value = value;
    }

    handleAvatorBadge(badge) {
        badge.classList.add("text-bg-secondary");
        badge.innerHTML = this.value;
    }

    handleProfileBadge(button) {
        button.classList.add("btn-outline-secondary");
        button.innerHTML = this.value;
    }

}

class Role {
    
    static roleList = [new Admin('admin'), new Helper('helper'), new Visitor('visitor')]

    constructor() {

    }

    static getRole(roleValue) {
        const role = Role.roleList.find(role => role.value === roleValue);
        return role || null;
    }

}