import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import api from "@/utils/api";
const router = useRouter();
const loading = ref(false);
const submitting = ref(false);
const profile = ref({
    id: null,
    name: "",
    mobile: "",
    status_text: "",
    balance: 0,
});
const form = ref({
    old_password: "",
    new_password: "",
    confirm_password: "",
});
const formRef = ref();
const rules = {
    old_password: [{ required: true, message: "请输入当前密码", trigger: "blur" }],
    new_password: [
        { required: true, message: "请输入新密码", trigger: "blur" },
        {
            min: 6,
            message: "新密码长度不能少于 6 位",
            trigger: "blur",
        },
    ],
    confirm_password: [
        { required: true, message: "请确认新密码", trigger: "blur" },
        {
            validator: (_rule, value, callback) => {
                if (!value) {
                    callback(new Error("请确认新密码"));
                }
                else if (value !== form.value.new_password) {
                    callback(new Error("两次输入的新密码不一致"));
                }
                else {
                    callback();
                }
            },
            trigger: "blur",
        },
    ],
};
const avatarText = computed(() => {
    if (profile.value.name) {
        return profile.value.name.slice(-2);
    }
    if (profile.value.mobile) {
        return profile.value.mobile.slice(-2);
    }
    return "会员";
});
async function loadProfile() {
    loading.value = true;
    try {
        const res = await api.get("/member/profile");
        const p = res.data || {};
        profile.value = {
            id: p.id ?? null,
            name: p.name || "",
            mobile: p.mobile || p.phone || "",
            status_text: p.status_text || "已启用",
            balance: Number(p.balance ?? 0),
        };
    }
    catch (err) {
        console.error(err);
        const msg = err?.response?.data?.detail || "加载账号信息失败";
        ElMessage.error(msg);
    }
    finally {
        loading.value = false;
    }
}
function onReset() {
    form.value.old_password = "";
    form.value.new_password = "";
    form.value.confirm_password = "";
}
async function onSubmit() {
    if (!formRef.value)
        return;
    await formRef.value.validate(async (valid) => {
        if (!valid)
            return;
        submitting.value = true;
        try {
            await api.post("/member/change-password", {
                old_password: form.value.old_password,
                new_password: form.value.new_password,
            });
            ElMessage.success("密码修改成功，请使用新密码重新登录");
            // 简单处理：清掉本地 token，跳回登录页
            localStorage.removeItem("member_token");
            router.push({ path: "/login" });
        }
        catch (err) {
            console.error(err);
            const msg = err?.response?.data?.detail || "修改密码失败";
            ElMessage.error(msg);
        }
        finally {
            submitting.value = false;
        }
    });
}
function logout() {
    localStorage.removeItem("member_token");
    router.push({ path: "/login" });
}
onMounted(() => {
    loadProfile();
});
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {
    ...{},
    ...{},
};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['page-header']} */ ;
/** @type {__VLS_StyleScopedClasses['page-header']} */ ;
/** @type {__VLS_StyleScopedClasses['tips']} */ ;
/** @type {__VLS_StyleScopedClasses['info-main']} */ ;
/** @type {__VLS_StyleScopedClasses['info-main']} */ ;
/** @type {__VLS_StyleScopedClasses['info-main']} */ ;
/** @type {__VLS_StyleScopedClasses['info-main']} */ ;
/** @type {__VLS_StyleScopedClasses['logout-block']} */ ;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "account-page" },
});
__VLS_asFunctionalDirective(__VLS_directives.vLoading)(null, { ...__VLS_directiveBindingRestFields, value: (__VLS_ctx.loading) }, null, null);
// @ts-ignore
[vLoading, loading,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "page-header" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
__VLS_asFunctionalElement(__VLS_intrinsics.h2, __VLS_intrinsics.h2)({});
__VLS_asFunctionalElement(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
if (__VLS_ctx.profile.status_text === '已启用') {
    // @ts-ignore
    [profile,];
    const __VLS_0 = {}.ElTag;
    /** @type {[typeof __VLS_components.ElTag, typeof __VLS_components.elTag, typeof __VLS_components.ElTag, typeof __VLS_components.elTag, ]} */ ;
    // @ts-ignore
    ElTag;
    // @ts-ignore
    const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({
        type: "success",
        size: "small",
    }));
    const __VLS_2 = __VLS_1({
        type: "success",
        size: "small",
    }, ...__VLS_functionalComponentArgsRest(__VLS_1));
    const { default: __VLS_4 } = __VLS_3.slots;
    (__VLS_ctx.profile.status_text);
    // @ts-ignore
    [profile,];
    var __VLS_3;
}
else {
    const __VLS_5 = {}.ElTag;
    /** @type {[typeof __VLS_components.ElTag, typeof __VLS_components.elTag, typeof __VLS_components.ElTag, typeof __VLS_components.elTag, ]} */ ;
    // @ts-ignore
    ElTag;
    // @ts-ignore
    const __VLS_6 = __VLS_asFunctionalComponent(__VLS_5, new __VLS_5({
        type: "danger",
        size: "small",
    }));
    const __VLS_7 = __VLS_6({
        type: "danger",
        size: "small",
    }, ...__VLS_functionalComponentArgsRest(__VLS_6));
    const { default: __VLS_9 } = __VLS_8.slots;
    (__VLS_ctx.profile.status_text || "未知状态");
    // @ts-ignore
    [profile,];
    var __VLS_8;
}
const __VLS_10 = {}.ElRow;
/** @type {[typeof __VLS_components.ElRow, typeof __VLS_components.elRow, typeof __VLS_components.ElRow, typeof __VLS_components.elRow, ]} */ ;
// @ts-ignore
ElRow;
// @ts-ignore
const __VLS_11 = __VLS_asFunctionalComponent(__VLS_10, new __VLS_10({
    gutter: (20),
}));
const __VLS_12 = __VLS_11({
    gutter: (20),
}, ...__VLS_functionalComponentArgsRest(__VLS_11));
const { default: __VLS_14 } = __VLS_13.slots;
const __VLS_15 = {}.ElCol;
/** @type {[typeof __VLS_components.ElCol, typeof __VLS_components.elCol, typeof __VLS_components.ElCol, typeof __VLS_components.elCol, ]} */ ;
// @ts-ignore
ElCol;
// @ts-ignore
const __VLS_16 = __VLS_asFunctionalComponent(__VLS_15, new __VLS_15({
    span: (14),
}));
const __VLS_17 = __VLS_16({
    span: (14),
}, ...__VLS_functionalComponentArgsRest(__VLS_16));
const { default: __VLS_19 } = __VLS_18.slots;
const __VLS_20 = {}.ElCard;
/** @type {[typeof __VLS_components.ElCard, typeof __VLS_components.elCard, typeof __VLS_components.ElCard, typeof __VLS_components.elCard, ]} */ ;
// @ts-ignore
ElCard;
// @ts-ignore
const __VLS_21 = __VLS_asFunctionalComponent(__VLS_20, new __VLS_20({
    shadow: "hover",
    ...{ class: "form-card" },
}));
const __VLS_22 = __VLS_21({
    shadow: "hover",
    ...{ class: "form-card" },
}, ...__VLS_functionalComponentArgsRest(__VLS_21));
const { default: __VLS_24 } = __VLS_23.slots;
{
    const { header: __VLS_25 } = __VLS_23.slots;
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "card-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "card-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "card-sub" },
    });
    (__VLS_ctx.profile.mobile || "-");
    // @ts-ignore
    [profile,];
}
const __VLS_26 = {}.ElForm;
/** @type {[typeof __VLS_components.ElForm, typeof __VLS_components.elForm, typeof __VLS_components.ElForm, typeof __VLS_components.elForm, ]} */ ;
// @ts-ignore
ElForm;
// @ts-ignore
const __VLS_27 = __VLS_asFunctionalComponent(__VLS_26, new __VLS_26({
    ref: "formRef",
    model: (__VLS_ctx.form),
    rules: (__VLS_ctx.rules),
    labelWidth: "100px",
    size: "large",
    ...{ class: "password-form" },
}));
const __VLS_28 = __VLS_27({
    ref: "formRef",
    model: (__VLS_ctx.form),
    rules: (__VLS_ctx.rules),
    labelWidth: "100px",
    size: "large",
    ...{ class: "password-form" },
}, ...__VLS_functionalComponentArgsRest(__VLS_27));
/** @type {typeof __VLS_ctx.formRef} */ ;
var __VLS_30 = {};
const { default: __VLS_32 } = __VLS_29.slots;
// @ts-ignore
[form, rules, formRef,];
const __VLS_33 = {}.ElFormItem;
/** @type {[typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, ]} */ ;
// @ts-ignore
ElFormItem;
// @ts-ignore
const __VLS_34 = __VLS_asFunctionalComponent(__VLS_33, new __VLS_33({
    label: "当前密码",
    prop: "old_password",
}));
const __VLS_35 = __VLS_34({
    label: "当前密码",
    prop: "old_password",
}, ...__VLS_functionalComponentArgsRest(__VLS_34));
const { default: __VLS_37 } = __VLS_36.slots;
const __VLS_38 = {}.ElInput;
/** @type {[typeof __VLS_components.ElInput, typeof __VLS_components.elInput, ]} */ ;
// @ts-ignore
ElInput;
// @ts-ignore
const __VLS_39 = __VLS_asFunctionalComponent(__VLS_38, new __VLS_38({
    modelValue: (__VLS_ctx.form.old_password),
    type: "password",
    showPassword: true,
    autocomplete: "current-password",
    placeholder: "请输入当前登录密码",
}));
const __VLS_40 = __VLS_39({
    modelValue: (__VLS_ctx.form.old_password),
    type: "password",
    showPassword: true,
    autocomplete: "current-password",
    placeholder: "请输入当前登录密码",
}, ...__VLS_functionalComponentArgsRest(__VLS_39));
// @ts-ignore
[form,];
var __VLS_36;
const __VLS_43 = {}.ElFormItem;
/** @type {[typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, ]} */ ;
// @ts-ignore
ElFormItem;
// @ts-ignore
const __VLS_44 = __VLS_asFunctionalComponent(__VLS_43, new __VLS_43({
    label: "新密码",
    prop: "new_password",
}));
const __VLS_45 = __VLS_44({
    label: "新密码",
    prop: "new_password",
}, ...__VLS_functionalComponentArgsRest(__VLS_44));
const { default: __VLS_47 } = __VLS_46.slots;
const __VLS_48 = {}.ElInput;
/** @type {[typeof __VLS_components.ElInput, typeof __VLS_components.elInput, ]} */ ;
// @ts-ignore
ElInput;
// @ts-ignore
const __VLS_49 = __VLS_asFunctionalComponent(__VLS_48, new __VLS_48({
    modelValue: (__VLS_ctx.form.new_password),
    type: "password",
    showPassword: true,
    autocomplete: "new-password",
    placeholder: "请输入新密码，至少 6 位",
}));
const __VLS_50 = __VLS_49({
    modelValue: (__VLS_ctx.form.new_password),
    type: "password",
    showPassword: true,
    autocomplete: "new-password",
    placeholder: "请输入新密码，至少 6 位",
}, ...__VLS_functionalComponentArgsRest(__VLS_49));
// @ts-ignore
[form,];
var __VLS_46;
const __VLS_53 = {}.ElFormItem;
/** @type {[typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, ]} */ ;
// @ts-ignore
ElFormItem;
// @ts-ignore
const __VLS_54 = __VLS_asFunctionalComponent(__VLS_53, new __VLS_53({
    label: "确认新密码",
    prop: "confirm_password",
}));
const __VLS_55 = __VLS_54({
    label: "确认新密码",
    prop: "confirm_password",
}, ...__VLS_functionalComponentArgsRest(__VLS_54));
const { default: __VLS_57 } = __VLS_56.slots;
const __VLS_58 = {}.ElInput;
/** @type {[typeof __VLS_components.ElInput, typeof __VLS_components.elInput, ]} */ ;
// @ts-ignore
ElInput;
// @ts-ignore
const __VLS_59 = __VLS_asFunctionalComponent(__VLS_58, new __VLS_58({
    modelValue: (__VLS_ctx.form.confirm_password),
    type: "password",
    showPassword: true,
    autocomplete: "new-password",
    placeholder: "请再次输入新密码",
}));
const __VLS_60 = __VLS_59({
    modelValue: (__VLS_ctx.form.confirm_password),
    type: "password",
    showPassword: true,
    autocomplete: "new-password",
    placeholder: "请再次输入新密码",
}, ...__VLS_functionalComponentArgsRest(__VLS_59));
// @ts-ignore
[form,];
var __VLS_56;
const __VLS_63 = {}.ElFormItem;
/** @type {[typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, ]} */ ;
// @ts-ignore
ElFormItem;
// @ts-ignore
const __VLS_64 = __VLS_asFunctionalComponent(__VLS_63, new __VLS_63({}));
const __VLS_65 = __VLS_64({}, ...__VLS_functionalComponentArgsRest(__VLS_64));
const { default: __VLS_67 } = __VLS_66.slots;
const __VLS_68 = {}.ElButton;
/** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
// @ts-ignore
ElButton;
// @ts-ignore
const __VLS_69 = __VLS_asFunctionalComponent(__VLS_68, new __VLS_68({
    ...{ 'onClick': {} },
    type: "primary",
    loading: (__VLS_ctx.submitting),
}));
const __VLS_70 = __VLS_69({
    ...{ 'onClick': {} },
    type: "primary",
    loading: (__VLS_ctx.submitting),
}, ...__VLS_functionalComponentArgsRest(__VLS_69));
let __VLS_72;
let __VLS_73;
const __VLS_74 = ({ click: {} },
    { onClick: (__VLS_ctx.onSubmit) });
const { default: __VLS_75 } = __VLS_71.slots;
// @ts-ignore
[submitting, onSubmit,];
var __VLS_71;
const __VLS_76 = {}.ElButton;
/** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
// @ts-ignore
ElButton;
// @ts-ignore
const __VLS_77 = __VLS_asFunctionalComponent(__VLS_76, new __VLS_76({
    ...{ 'onClick': {} },
}));
const __VLS_78 = __VLS_77({
    ...{ 'onClick': {} },
}, ...__VLS_functionalComponentArgsRest(__VLS_77));
let __VLS_80;
let __VLS_81;
const __VLS_82 = ({ click: {} },
    { onClick: (__VLS_ctx.onReset) });
const { default: __VLS_83 } = __VLS_79.slots;
// @ts-ignore
[onReset,];
var __VLS_79;
var __VLS_66;
var __VLS_29;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "tips" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "tips-title" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.ul, __VLS_intrinsics.ul)({});
__VLS_asFunctionalElement(__VLS_intrinsics.li, __VLS_intrinsics.li)({});
__VLS_asFunctionalElement(__VLS_intrinsics.li, __VLS_intrinsics.li)({});
__VLS_asFunctionalElement(__VLS_intrinsics.li, __VLS_intrinsics.li)({});
var __VLS_23;
var __VLS_18;
const __VLS_84 = {}.ElCol;
/** @type {[typeof __VLS_components.ElCol, typeof __VLS_components.elCol, typeof __VLS_components.ElCol, typeof __VLS_components.elCol, ]} */ ;
// @ts-ignore
ElCol;
// @ts-ignore
const __VLS_85 = __VLS_asFunctionalComponent(__VLS_84, new __VLS_84({
    span: (10),
}));
const __VLS_86 = __VLS_85({
    span: (10),
}, ...__VLS_functionalComponentArgsRest(__VLS_85));
const { default: __VLS_88 } = __VLS_87.slots;
const __VLS_89 = {}.ElCard;
/** @type {[typeof __VLS_components.ElCard, typeof __VLS_components.elCard, typeof __VLS_components.ElCard, typeof __VLS_components.elCard, ]} */ ;
// @ts-ignore
ElCard;
// @ts-ignore
const __VLS_90 = __VLS_asFunctionalComponent(__VLS_89, new __VLS_89({
    shadow: "hover",
    ...{ class: "info-card" },
}));
const __VLS_91 = __VLS_90({
    shadow: "hover",
    ...{ class: "info-card" },
}, ...__VLS_functionalComponentArgsRest(__VLS_90));
const { default: __VLS_93 } = __VLS_92.slots;
{
    const { header: __VLS_94 } = __VLS_92.slots;
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "card-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "card-title" },
    });
}
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "info-body" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "avatar-circle" },
});
(__VLS_ctx.avatarText);
// @ts-ignore
[avatarText,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "info-main" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "name" },
});
(__VLS_ctx.profile.name || "会员用户");
// @ts-ignore
[profile,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "mobile" },
});
(__VLS_ctx.profile.mobile || "-");
// @ts-ignore
[profile,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "status" },
});
if (__VLS_ctx.profile.status_text === '已启用') {
    // @ts-ignore
    [profile,];
    __VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    (__VLS_ctx.profile.status_text || "未知");
    // @ts-ignore
    [profile,];
}
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "balance" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({
    ...{ class: "amount" },
});
(__VLS_ctx.profile.balance.toFixed(2));
// @ts-ignore
[profile,];
const __VLS_95 = {}.ElDivider;
/** @type {[typeof __VLS_components.ElDivider, typeof __VLS_components.elDivider, ]} */ ;
// @ts-ignore
ElDivider;
// @ts-ignore
const __VLS_96 = __VLS_asFunctionalComponent(__VLS_95, new __VLS_95({}));
const __VLS_97 = __VLS_96({}, ...__VLS_functionalComponentArgsRest(__VLS_96));
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "logout-block" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "tip" },
});
const __VLS_100 = {}.ElButton;
/** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
// @ts-ignore
ElButton;
// @ts-ignore
const __VLS_101 = __VLS_asFunctionalComponent(__VLS_100, new __VLS_100({
    ...{ 'onClick': {} },
    type: "danger",
    plain: true,
}));
const __VLS_102 = __VLS_101({
    ...{ 'onClick': {} },
    type: "danger",
    plain: true,
}, ...__VLS_functionalComponentArgsRest(__VLS_101));
let __VLS_104;
let __VLS_105;
const __VLS_106 = ({ click: {} },
    { onClick: (__VLS_ctx.logout) });
const { default: __VLS_107 } = __VLS_103.slots;
// @ts-ignore
[logout,];
var __VLS_103;
var __VLS_92;
var __VLS_87;
var __VLS_13;
/** @type {__VLS_StyleScopedClasses['account-page']} */ ;
/** @type {__VLS_StyleScopedClasses['page-header']} */ ;
/** @type {__VLS_StyleScopedClasses['form-card']} */ ;
/** @type {__VLS_StyleScopedClasses['card-header']} */ ;
/** @type {__VLS_StyleScopedClasses['card-title']} */ ;
/** @type {__VLS_StyleScopedClasses['card-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['password-form']} */ ;
/** @type {__VLS_StyleScopedClasses['tips']} */ ;
/** @type {__VLS_StyleScopedClasses['tips-title']} */ ;
/** @type {__VLS_StyleScopedClasses['info-card']} */ ;
/** @type {__VLS_StyleScopedClasses['card-header']} */ ;
/** @type {__VLS_StyleScopedClasses['card-title']} */ ;
/** @type {__VLS_StyleScopedClasses['info-body']} */ ;
/** @type {__VLS_StyleScopedClasses['avatar-circle']} */ ;
/** @type {__VLS_StyleScopedClasses['info-main']} */ ;
/** @type {__VLS_StyleScopedClasses['name']} */ ;
/** @type {__VLS_StyleScopedClasses['mobile']} */ ;
/** @type {__VLS_StyleScopedClasses['status']} */ ;
/** @type {__VLS_StyleScopedClasses['balance']} */ ;
/** @type {__VLS_StyleScopedClasses['amount']} */ ;
/** @type {__VLS_StyleScopedClasses['logout-block']} */ ;
/** @type {__VLS_StyleScopedClasses['tip']} */ ;
// @ts-ignore
var __VLS_31 = __VLS_30;
const __VLS_export = (await import('vue')).defineComponent({});
export default {};
