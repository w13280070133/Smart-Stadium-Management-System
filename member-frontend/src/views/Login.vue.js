import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import api from "@/utils/api";
import { setMemberToken, setMemberInfo, clearMemberAuth, } from "@/utils/auth";
const router = useRouter();
const form = reactive({
    phone: "",
    password: "",
});
const loading = ref(false);
async function handleLogin() {
    if (!form.phone || !form.password) {
        ElMessage.error("请输入手机号和密码");
        return;
    }
    loading.value = true;
    try {
        const params = new URLSearchParams();
        params.append("username", form.phone);
        params.append("password", form.password);
        const res = await api.post("/member-auth/token", params, {
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
        });
        const data = res.data;
        setMemberToken(data.access_token);
        setMemberInfo(data.member);
        ElMessage.success("登录成功");
        router.push("/home");
    }
    catch (e) {
        clearMemberAuth();
        ElMessage.error(e?.response?.data?.detail || "登录失败，请稍后重试");
    }
    finally {
        loading.value = false;
    }
}
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {
    ...{},
    ...{},
};
let __VLS_components;
let __VLS_directives;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "login-page" },
});
const __VLS_0 = {}.ElCard;
/** @type {[typeof __VLS_components.ElCard, typeof __VLS_components.elCard, typeof __VLS_components.ElCard, typeof __VLS_components.elCard, ]} */ ;
// @ts-ignore
ElCard;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({
    ...{ class: "login-card" },
    shadow: "hover",
}));
const __VLS_2 = __VLS_1({
    ...{ class: "login-card" },
    shadow: "hover",
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
const { default: __VLS_4 } = __VLS_3.slots;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "title" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "sub-title" },
});
const __VLS_5 = {}.ElForm;
/** @type {[typeof __VLS_components.ElForm, typeof __VLS_components.elForm, typeof __VLS_components.ElForm, typeof __VLS_components.elForm, ]} */ ;
// @ts-ignore
ElForm;
// @ts-ignore
const __VLS_6 = __VLS_asFunctionalComponent(__VLS_5, new __VLS_5({
    ...{ 'onKeyup': {} },
    model: (__VLS_ctx.form),
    ...{ class: "form" },
}));
const __VLS_7 = __VLS_6({
    ...{ 'onKeyup': {} },
    model: (__VLS_ctx.form),
    ...{ class: "form" },
}, ...__VLS_functionalComponentArgsRest(__VLS_6));
let __VLS_9;
let __VLS_10;
const __VLS_11 = ({ keyup: {} },
    { onKeyup: (__VLS_ctx.handleLogin) });
const { default: __VLS_12 } = __VLS_8.slots;
// @ts-ignore
[form, handleLogin,];
const __VLS_13 = {}.ElFormItem;
/** @type {[typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, ]} */ ;
// @ts-ignore
ElFormItem;
// @ts-ignore
const __VLS_14 = __VLS_asFunctionalComponent(__VLS_13, new __VLS_13({}));
const __VLS_15 = __VLS_14({}, ...__VLS_functionalComponentArgsRest(__VLS_14));
const { default: __VLS_17 } = __VLS_16.slots;
const __VLS_18 = {}.ElInput;
/** @type {[typeof __VLS_components.ElInput, typeof __VLS_components.elInput, ]} */ ;
// @ts-ignore
ElInput;
// @ts-ignore
const __VLS_19 = __VLS_asFunctionalComponent(__VLS_18, new __VLS_18({
    modelValue: (__VLS_ctx.form.phone),
    placeholder: "手机号",
    maxlength: "11",
}));
const __VLS_20 = __VLS_19({
    modelValue: (__VLS_ctx.form.phone),
    placeholder: "手机号",
    maxlength: "11",
}, ...__VLS_functionalComponentArgsRest(__VLS_19));
// @ts-ignore
[form,];
var __VLS_16;
const __VLS_23 = {}.ElFormItem;
/** @type {[typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, ]} */ ;
// @ts-ignore
ElFormItem;
// @ts-ignore
const __VLS_24 = __VLS_asFunctionalComponent(__VLS_23, new __VLS_23({}));
const __VLS_25 = __VLS_24({}, ...__VLS_functionalComponentArgsRest(__VLS_24));
const { default: __VLS_27 } = __VLS_26.slots;
const __VLS_28 = {}.ElInput;
/** @type {[typeof __VLS_components.ElInput, typeof __VLS_components.elInput, ]} */ ;
// @ts-ignore
ElInput;
// @ts-ignore
const __VLS_29 = __VLS_asFunctionalComponent(__VLS_28, new __VLS_28({
    modelValue: (__VLS_ctx.form.password),
    type: "password",
    showPassword: true,
    placeholder: "登录密码",
}));
const __VLS_30 = __VLS_29({
    modelValue: (__VLS_ctx.form.password),
    type: "password",
    showPassword: true,
    placeholder: "登录密码",
}, ...__VLS_functionalComponentArgsRest(__VLS_29));
// @ts-ignore
[form,];
var __VLS_26;
const __VLS_33 = {}.ElFormItem;
/** @type {[typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, ]} */ ;
// @ts-ignore
ElFormItem;
// @ts-ignore
const __VLS_34 = __VLS_asFunctionalComponent(__VLS_33, new __VLS_33({}));
const __VLS_35 = __VLS_34({}, ...__VLS_functionalComponentArgsRest(__VLS_34));
const { default: __VLS_37 } = __VLS_36.slots;
const __VLS_38 = {}.ElButton;
/** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
// @ts-ignore
ElButton;
// @ts-ignore
const __VLS_39 = __VLS_asFunctionalComponent(__VLS_38, new __VLS_38({
    ...{ 'onClick': {} },
    type: "primary",
    ...{ class: "btn" },
    loading: (__VLS_ctx.loading),
}));
const __VLS_40 = __VLS_39({
    ...{ 'onClick': {} },
    type: "primary",
    ...{ class: "btn" },
    loading: (__VLS_ctx.loading),
}, ...__VLS_functionalComponentArgsRest(__VLS_39));
let __VLS_42;
let __VLS_43;
const __VLS_44 = ({ click: {} },
    { onClick: (__VLS_ctx.handleLogin) });
const { default: __VLS_45 } = __VLS_41.slots;
// @ts-ignore
[handleLogin, loading,];
var __VLS_41;
var __VLS_36;
var __VLS_8;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "tip" },
});
var __VLS_3;
/** @type {__VLS_StyleScopedClasses['login-page']} */ ;
/** @type {__VLS_StyleScopedClasses['login-card']} */ ;
/** @type {__VLS_StyleScopedClasses['title']} */ ;
/** @type {__VLS_StyleScopedClasses['sub-title']} */ ;
/** @type {__VLS_StyleScopedClasses['form']} */ ;
/** @type {__VLS_StyleScopedClasses['btn']} */ ;
/** @type {__VLS_StyleScopedClasses['tip']} */ ;
const __VLS_export = (await import('vue')).defineComponent({});
export default {};
