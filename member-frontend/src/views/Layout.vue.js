import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
const route = useRoute();
const router = useRouter();
const activeMenu = computed(() => {
    return route.path.startsWith("/") ? route.path : `/${route.path}`;
});
const displayName = computed(() => {
    const name = localStorage.getItem("member_name") ||
        localStorage.getItem("memberName") ||
        "";
    const cardNo = localStorage.getItem("member_card_no") ||
        localStorage.getItem("memberCardNo") ||
        "";
    if (name && cardNo) {
        return `${name} (${cardNo})`;
    }
    if (name)
        return name;
    return "会员用户";
});
const handleLogout = () => {
    localStorage.clear();
    router.push("/login");
};
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {
    ...{},
    ...{},
};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['title-block']} */ ;
/** @type {__VLS_StyleScopedClasses['member-menu']} */ ;
const __VLS_0 = {}.ElContainer;
/** @type {[typeof __VLS_components.ElContainer, typeof __VLS_components.elContainer, typeof __VLS_components.ElContainer, typeof __VLS_components.elContainer, ]} */ ;
// @ts-ignore
ElContainer;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({
    ...{ class: "member-layout" },
}));
const __VLS_2 = __VLS_1({
    ...{ class: "member-layout" },
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
var __VLS_4 = {};
const { default: __VLS_5 } = __VLS_3.slots;
const __VLS_6 = {}.ElHeader;
/** @type {[typeof __VLS_components.ElHeader, typeof __VLS_components.elHeader, typeof __VLS_components.ElHeader, typeof __VLS_components.elHeader, ]} */ ;
// @ts-ignore
ElHeader;
// @ts-ignore
const __VLS_7 = __VLS_asFunctionalComponent(__VLS_6, new __VLS_6({
    ...{ class: "member-header" },
}));
const __VLS_8 = __VLS_7({
    ...{ class: "member-header" },
}, ...__VLS_functionalComponentArgsRest(__VLS_7));
const { default: __VLS_10 } = __VLS_9.slots;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "logo-area" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "logo-circle" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({
    ...{ class: "logo-text" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "title-block" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "system-name" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "system-sub" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "user-area" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({
    ...{ class: "user-name" },
});
(__VLS_ctx.displayName);
// @ts-ignore
[displayName,];
const __VLS_11 = {}.ElDivider;
/** @type {[typeof __VLS_components.ElDivider, typeof __VLS_components.elDivider, ]} */ ;
// @ts-ignore
ElDivider;
// @ts-ignore
const __VLS_12 = __VLS_asFunctionalComponent(__VLS_11, new __VLS_11({
    direction: "vertical",
}));
const __VLS_13 = __VLS_12({
    direction: "vertical",
}, ...__VLS_functionalComponentArgsRest(__VLS_12));
const __VLS_16 = {}.ElButton;
/** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
// @ts-ignore
ElButton;
// @ts-ignore
const __VLS_17 = __VLS_asFunctionalComponent(__VLS_16, new __VLS_16({
    ...{ 'onClick': {} },
    type: "text",
}));
const __VLS_18 = __VLS_17({
    ...{ 'onClick': {} },
    type: "text",
}, ...__VLS_functionalComponentArgsRest(__VLS_17));
let __VLS_20;
let __VLS_21;
const __VLS_22 = ({ click: {} },
    { onClick: (__VLS_ctx.handleLogout) });
const { default: __VLS_23 } = __VLS_19.slots;
// @ts-ignore
[handleLogout,];
var __VLS_19;
var __VLS_9;
const __VLS_24 = {}.ElContainer;
/** @type {[typeof __VLS_components.ElContainer, typeof __VLS_components.elContainer, typeof __VLS_components.ElContainer, typeof __VLS_components.elContainer, ]} */ ;
// @ts-ignore
ElContainer;
// @ts-ignore
const __VLS_25 = __VLS_asFunctionalComponent(__VLS_24, new __VLS_24({}));
const __VLS_26 = __VLS_25({}, ...__VLS_functionalComponentArgsRest(__VLS_25));
const { default: __VLS_28 } = __VLS_27.slots;
const __VLS_29 = {}.ElAside;
/** @type {[typeof __VLS_components.ElAside, typeof __VLS_components.elAside, typeof __VLS_components.ElAside, typeof __VLS_components.elAside, ]} */ ;
// @ts-ignore
ElAside;
// @ts-ignore
const __VLS_30 = __VLS_asFunctionalComponent(__VLS_29, new __VLS_29({
    width: "200px",
    ...{ class: "member-sider" },
}));
const __VLS_31 = __VLS_30({
    width: "200px",
    ...{ class: "member-sider" },
}, ...__VLS_functionalComponentArgsRest(__VLS_30));
const { default: __VLS_33 } = __VLS_32.slots;
const __VLS_34 = {}.ElMenu;
/** @type {[typeof __VLS_components.ElMenu, typeof __VLS_components.elMenu, typeof __VLS_components.ElMenu, typeof __VLS_components.elMenu, ]} */ ;
// @ts-ignore
ElMenu;
// @ts-ignore
const __VLS_35 = __VLS_asFunctionalComponent(__VLS_34, new __VLS_34({
    ...{ class: "member-menu" },
    defaultActive: (__VLS_ctx.activeMenu),
    router: true,
}));
const __VLS_36 = __VLS_35({
    ...{ class: "member-menu" },
    defaultActive: (__VLS_ctx.activeMenu),
    router: true,
}, ...__VLS_functionalComponentArgsRest(__VLS_35));
const { default: __VLS_38 } = __VLS_37.slots;
// @ts-ignore
[activeMenu,];
const __VLS_39 = {}.ElMenuItem;
/** @type {[typeof __VLS_components.ElMenuItem, typeof __VLS_components.elMenuItem, typeof __VLS_components.ElMenuItem, typeof __VLS_components.elMenuItem, ]} */ ;
// @ts-ignore
ElMenuItem;
// @ts-ignore
const __VLS_40 = __VLS_asFunctionalComponent(__VLS_39, new __VLS_39({
    index: "/home",
}));
const __VLS_41 = __VLS_40({
    index: "/home",
}, ...__VLS_functionalComponentArgsRest(__VLS_40));
const { default: __VLS_43 } = __VLS_42.slots;
__VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
var __VLS_42;
const __VLS_44 = {}.ElMenuItem;
/** @type {[typeof __VLS_components.ElMenuItem, typeof __VLS_components.elMenuItem, typeof __VLS_components.ElMenuItem, typeof __VLS_components.elMenuItem, ]} */ ;
// @ts-ignore
ElMenuItem;
// @ts-ignore
const __VLS_45 = __VLS_asFunctionalComponent(__VLS_44, new __VLS_44({
    index: "/reservations",
}));
const __VLS_46 = __VLS_45({
    index: "/reservations",
}, ...__VLS_functionalComponentArgsRest(__VLS_45));
const { default: __VLS_48 } = __VLS_47.slots;
__VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
var __VLS_47;
const __VLS_49 = {}.ElMenuItem;
/** @type {[typeof __VLS_components.ElMenuItem, typeof __VLS_components.elMenuItem, typeof __VLS_components.ElMenuItem, typeof __VLS_components.elMenuItem, ]} */ ;
// @ts-ignore
ElMenuItem;
// @ts-ignore
const __VLS_50 = __VLS_asFunctionalComponent(__VLS_49, new __VLS_49({
    index: "/orders",
}));
const __VLS_51 = __VLS_50({
    index: "/orders",
}, ...__VLS_functionalComponentArgsRest(__VLS_50));
const { default: __VLS_53 } = __VLS_52.slots;
__VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
var __VLS_52;
const __VLS_54 = {}.ElMenuItem;
/** @type {[typeof __VLS_components.ElMenuItem, typeof __VLS_components.elMenuItem, typeof __VLS_components.ElMenuItem, typeof __VLS_components.elMenuItem, ]} */ ;
// @ts-ignore
ElMenuItem;
// @ts-ignore
const __VLS_55 = __VLS_asFunctionalComponent(__VLS_54, new __VLS_54({
    index: "/notifications",
}));
const __VLS_56 = __VLS_55({
    index: "/notifications",
}, ...__VLS_functionalComponentArgsRest(__VLS_55));
const { default: __VLS_58 } = __VLS_57.slots;
__VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
var __VLS_57;
const __VLS_59 = {}.ElMenuItem;
/** @type {[typeof __VLS_components.ElMenuItem, typeof __VLS_components.elMenuItem, typeof __VLS_components.ElMenuItem, typeof __VLS_components.elMenuItem, ]} */ ;
// @ts-ignore
ElMenuItem;
// @ts-ignore
const __VLS_60 = __VLS_asFunctionalComponent(__VLS_59, new __VLS_59({
    index: "/account",
}));
const __VLS_61 = __VLS_60({
    index: "/account",
}, ...__VLS_functionalComponentArgsRest(__VLS_60));
const { default: __VLS_63 } = __VLS_62.slots;
__VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
var __VLS_62;
var __VLS_37;
var __VLS_32;
const __VLS_64 = {}.ElMain;
/** @type {[typeof __VLS_components.ElMain, typeof __VLS_components.elMain, typeof __VLS_components.ElMain, typeof __VLS_components.elMain, ]} */ ;
// @ts-ignore
ElMain;
// @ts-ignore
const __VLS_65 = __VLS_asFunctionalComponent(__VLS_64, new __VLS_64({
    ...{ class: "member-main" },
}));
const __VLS_66 = __VLS_65({
    ...{ class: "member-main" },
}, ...__VLS_functionalComponentArgsRest(__VLS_65));
const { default: __VLS_68 } = __VLS_67.slots;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "page-wrapper" },
});
const __VLS_69 = {}.RouterView;
/** @type {[typeof __VLS_components.RouterView, typeof __VLS_components.routerView, ]} */ ;
// @ts-ignore
RouterView;
// @ts-ignore
const __VLS_70 = __VLS_asFunctionalComponent(__VLS_69, new __VLS_69({}));
const __VLS_71 = __VLS_70({}, ...__VLS_functionalComponentArgsRest(__VLS_70));
var __VLS_67;
var __VLS_27;
var __VLS_3;
/** @type {__VLS_StyleScopedClasses['member-layout']} */ ;
/** @type {__VLS_StyleScopedClasses['member-header']} */ ;
/** @type {__VLS_StyleScopedClasses['logo-area']} */ ;
/** @type {__VLS_StyleScopedClasses['logo-circle']} */ ;
/** @type {__VLS_StyleScopedClasses['logo-text']} */ ;
/** @type {__VLS_StyleScopedClasses['title-block']} */ ;
/** @type {__VLS_StyleScopedClasses['system-name']} */ ;
/** @type {__VLS_StyleScopedClasses['system-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['user-area']} */ ;
/** @type {__VLS_StyleScopedClasses['user-name']} */ ;
/** @type {__VLS_StyleScopedClasses['member-sider']} */ ;
/** @type {__VLS_StyleScopedClasses['member-menu']} */ ;
/** @type {__VLS_StyleScopedClasses['member-main']} */ ;
/** @type {__VLS_StyleScopedClasses['page-wrapper']} */ ;
const __VLS_export = (await import('vue')).defineComponent({});
export default {};
